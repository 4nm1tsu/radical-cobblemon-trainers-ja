TAG=$(git describe --tags --abbrev=0)
echo "Using tag: $TAG"
zip -r "../radical-cobblemon-trainers-ja$TAG.zip" pack.mcmeta assets data -x "*.git*" -x "makezip.sh" -x "trainers_original" -x "localize.py" -x "title_map.json"
