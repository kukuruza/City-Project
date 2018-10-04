#### Compute H from frame to map for a camera
```
python3 src/scenes/ComputePoseH.py --camera_id 691 --map_id 0 --update_map_json
```

#### Make one global map with all the cameras on them

```
python3 src/scenes/MakeGlobalVisibility.py \
  --bigpic_mapid 1 --logging 30 \
  --camera_ids 170 164 166 253 181 398 403 410 495 511 551 691 846 928
```