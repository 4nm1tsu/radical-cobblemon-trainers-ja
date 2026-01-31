
import json
import re
from pathlib import Path

# =========================
# Paths
# =========================
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "trainers_original"
OUTPUT_DIR = BASE_DIR / "data" / "rctmod" / "trainers"

# =========================
# Load maps
# =========================
with open(BASE_DIR / "title_map.json", encoding="utf-8") as f:
    TITLE_MAP = json.load(f)

with open(BASE_DIR / "proper_name_map.json", encoding="utf-8") as f:
    PROPER_NAME_MAP = json.load(f)

# =========================
# Utils
# =========================
def normalize_name(name: str):
    """
    Swimmer♂ David -> ("Swimmer", "MALE", "David")
    Tuber♀ Alice   -> ("Tuber", "FEMALE", "Alice")
    """
    m = re.match(r"^(Swimmer|Tuber)(♂|♀)\s+(.*)$", name)
    if m:
        title, mark, rest = m.groups()
        gender = "MALE" if mark == "♂" else "FEMALE"
        return title, gender, rest
    return None, None, name


def get_trainer_gender(trainer: dict):
    for p in trainer.get("team", []):
        g = p.get("gender")
        if g in ("MALE", "FEMALE"):
            return g
    return None


# =========================
# Core
# =========================
def localize_name(original_name: str, trainer: dict) -> str | None:

    # ---- 固有名 完全一致 ----
    if original_name in PROPER_NAME_MAP:
        return PROPER_NAME_MAP[original_name]

    # ---- 正規化（Swimmer♂ 等）----
    norm_title, norm_gender, normalized = normalize_name(original_name)

    # ---- title 決定 ----
    if norm_title:
        title = norm_title
        rest = normalized
    else:
        tokens = original_name.split()
        title = None
        rest = None

        for i in range(len(tokens), 0, -1):
            candidate = " ".join(tokens[:i])
            if candidate in TITLE_MAP:
                title = candidate
                rest = " ".join(tokens[i:])
                break

        if not title:
            print(f"[skip] title not found: {original_name}")
            return None

    title_entry = TITLE_MAP.get(title)

    # ---- 性別分岐 ----
    if isinstance(title_entry, dict):
        gender = norm_gender or get_trainer_gender(trainer)
        if not gender or gender not in title_entry:
            print(f"[skip] gender unknown: {original_name}")
            return None
        jp_title = title_entry[gender]
    else:
        jp_title = title_entry

    # ---- 名前部分 ----
    if not rest:
        return jp_title

    rest = rest.replace("&", "＆")

    names = [n.strip() for n in rest.split("＆")]
    jp_names = [PROPER_NAME_MAP.get(n, n) for n in names]

    return f"{jp_title} {'＆'.join(jp_names)}"


# =========================
# Main
# =========================
def main():
    print("script started")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = list(INPUT_DIR.glob("*.json"))
    print(f"json files found: {len(files)}")

    processed = 0
    skipped = 0

    for src in files:
        with open(src, encoding="utf-8") as f:
            data = json.load(f)

        original_name = data.get("name")
        if not original_name:
            skipped += 1
            continue

        localized = localize_name(original_name, data)

        if localized:
            data["name"] = localized
            processed += 1
            print(f"[ok] {original_name} -> {localized}")
        else:
            skipped += 1

        out = OUTPUT_DIR / src.name
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print("----")
    print(f"processed: {processed}")
    print(f"skipped:   {skipped}")


if __name__ == "__main__":
    main()

