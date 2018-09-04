City-Project
============

Analyze traffic given a set of optical cameras in urban areas

Necessary pip dependencies:
progressbar2
scipy
cv2
Pillow==2.6.0
simplejson
numpy

Dependencies for certain functions:
matplotlib
elasticsearch
scikit-image
imageio


## Labelme annotations
```
# Export for labelling.
modify \
    -i data/patches/Oct10-real/w55-e04.db 
    exportImagesToFolder --image_dir ~/src/labelme/LabelMeAnnotationTool/Images/w55-e04

# Import labelled.
modify \
   -i data/patches/Oct10-real/w55-e04.db \
   -o data/patches/Oct10-real/w55-e04-mask.db \
   importLabelme --in_annotations_dir ~/src/labelme/LabelMeAnnotationTool/Annotations/w55-e04 --merge_cars \
   polygonsToMasks --mask_name w55-e04mask.avi --overwrite_video --write_null_mask_entries
```

# Export dataset of car patches.
```
modify \
    -i data/databases/wpitch.db \
    filterUnknownNames \
    filterCustom --car_constraint "width > 55 AND height > 55 AND name IN ('van', 'taxi', 'sedan')" \
    filterByIntersection --intersection_thresh_perc 0.2 \
    expandBoxes --expand_perc 0.2 \
    filterByBorder \
    exportCarsToDataset --edges distort --target_width 64 --target_height 64 --patch_db_file data/patches/Oct10-real/w55-goodtypes-e04.db \
    deleteEmptyImages info
```

# Export video with boxes with car info where yaw is not null.
```
modify \
    -i data/patches/Oct10-real/w55-goodtypes-e04.db \
    filterCustom --car_constraint "yaw IS NOT NULL" \
    deleteEmptyImages \
    exportImagesWBoxes --out_videofile data/patches/Oct10-real/w55-goodtypes-e04-boxes-with-yaw.avi --with_car_info
```

# Display car patches which have a valid mask.
```
modify \
    -i data/patches/Oct10-real/w55-goodtypes-e04-filt-poly.db \
    filterCustom --image_constraint "maskfile IS NOT NULL" \
    display --masked
```

# Plotting functions.
```
modify -i data/databases/wpitch.db plotHistogram -x name --out_path data/databases/hist_name.eps --bins 50 --ylog --constraint 'name != "object"' --categorical
modify -i data/databases/wpitch.db plotHistogram -x width --out_path data/databases/hist_width.eps --bins 50 --ylog
modify -i data/databases/wpitch.db plotStrip -x "substr(imagefile, 14, 3)" -y pitch --out_path data/databases/strip_cam_pitch2.png
```

