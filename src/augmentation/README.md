Augmentation
============

## Running examples

```
python src/augmentation/MakePatches.py
```

```
python src/augmentation/ProcessFrame.py --video_dir augmentation/scenes/cam572/Nov28-10h
```

```
python src/augmentation/ProcessVideo.py --timeout 10 --job_file augmentation/jobs/572-Feb23-09h.json
```


# Running optimizer
```
python src/augmentation/OptimizeRenderer.py \
--ref_db_file databases/labelme/572-Oct30-17h-pair/parsed-taxi.db \
--back_file camdata/cam572/Oct30-17h/back.png \
--video_dir augmentation/scenes/cam572/Oct30-17h
```
