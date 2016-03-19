#!/bin/sh
num_occl=$1
sz=$2
  
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches_name train-taxi-5K-${sz}x${sz}-ocl${num_occl}      --target_width $sz --target_height $sz --expand_perc 0.3 --num_occluding $num_occl --collection_id 7c7c2b02ad5108fe5f9082491d52810
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches_name train-schoolbus-5K-${sz}x${sz}-ocl${num_occl} --target_width $sz --target_height $sz --expand_perc 0.3 --num_occluding $num_occl --collection_id uecadcbca-a400-428d-9240-a331ac5014f6
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches_name test-taxi-5K-${sz}x${sz}-ocl${num_occl}       --target_width $sz --target_height $sz --expand_perc 0.3 --num_occluding $num_occl --collection_id taxi-without-collection
$CITY_PATH/src/augmentation/MakePatches.py --number 5000 --num_per_session 50 --render PARALLEL --patches_name test-schoolbus-5K-${sz}x${sz}-ocl${num_occl}  --target_width $sz --target_height $sz --expand_perc 0.3 --num_occluding $num_occl --collection_id da6975e17daba42c84dbed50a1843204
