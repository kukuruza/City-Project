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


## Import labelme annotations
```
modify \
   -i data/patches/Oct10-real/w55-goodtypes-e04-filt.db \
   -o data/patches/Oct10-real/w55-goodtypes-e04-filt-poly.db \
   importLabelme --in_annotations_dir ~/src/labelme/LabelMeAnnotationTool/Annotations/w55-goodtypes-e04 --merge_cars \
   polygonsToMasks --mask_name w55-goodtypes-e04mask.avi --overwrite_video --write_null_mask_entries
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

