Augmentation
============

## To make patches:

```
python3 src/augmentation/render/MakePatches.py \
  -o data/augmentation/test/scenes.db \
  --num_sessions 100 --num_per_session 10 --num_occluding 5 --mode PARALLEL \
  --clause_main 'WHERE error IS NULL AND dims_L < 10' \
  --cad_db_path data/augmentation/CAD/collections_v1.db

modify -i data/patches/test/scenes.db \
  expandBoxes --expand_perc 0.2 \
  exportCarsToDataset --edges distort --target_width 64 --target_height 64 --patch_db_file data/patches/test/patches-w55-e04.db

python3 src/augmentation/render/SetPropertyAsName.py \
  --cad_db_path data/augmentation/CAD/collections_v1.db \
  --in_db_path data/patches/test/patches-w55-e04.db \
  --out_db_path data/patches/test/patches-w55-e04-name.db \
  --classes type1
```

```
python src/augmentation/ProcessFrame.py --video_dir augmentation/scenes/cam572/Nov28-10h
```

```
python src/augmentation/GenerateTraffic.py  --job_file augmentation/jobs/572-Feb23-09h-test.json --traffic_file augmentation/video/test/traffic.json
```

```
python src/augmentation/ProcessVideo.py --timeout 10 --job_file augmentation/jobs/572-Feb23-09h-test.json --traffic_file augmentation/video/test/traffic.json
```
