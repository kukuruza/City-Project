Augmentation
============

## To make patches:

```
python3 src/augmentation/render/MakePatches.py \
  -o data/augmentation/test/scenes.db \
  --num_sessions 100 --num_per_session 10 --num_occluding 5 --mode PARALLEL \
  --clause_main 'WHERE error IS NULL AND dims_L < 10' \
  --cad_db_path data/augmentation/CAD/collections_v1.db

python3 src/augmentation/render/SetPropertyAsName.py \
  --in_db_path  data/patches/Sept18-pitch5to35-1K/scenes.db \
  --out_db_path data/patches/Sept18-pitch5to35-1K/scenes-name.db \
  --cad_db_path data/augmentation/CAD/collections_v1.db \
  --classes type1 domain

modify \
  -i data/patches/Sept18-pitch5to35-1K/scenes-name.db \
  filterByBorder \
  expandBoxes --expand_perc 0.2 \
  exportCarsToDataset --edges distort --target_width 64 --target_height 64 \
    --patch_db_file data/patches/Sept18-pitch5to35-1K/patches-w55-e04.db 
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
