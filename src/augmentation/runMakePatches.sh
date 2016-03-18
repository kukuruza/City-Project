#!/bin/sh
num_occl=$1
  
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches-name train-taxi-5K-72x72-ocl0      --target_width 72 --target_height 72 --expand_perc 0.3 --num_occluding $num_occl --collection_id 7c7c2b02ad5108fe5f9082491d52810
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches-name train-schoolbus-5K-72x72-ocl0 --target_width 72 --target_height 72 --expand_perc 0.3 --num_occluding $num_occl --collection_id uecadcbca-a400-428d-9240-a331ac5014f6
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches-name test-taxi-5K-72x72-ocl0       --target_width 72 --target_height 72 --expand_perc 0.3 --num_occluding $num_occl --collection_id taxi-without-collection
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches-name test-schoolbus-5K-72x72-ocl0  --target_width 72 --target_height 72 --expand_perc 0.3 --num_occluding $num_occl --collection_id da6975e17daba42c84dbed50a1843204