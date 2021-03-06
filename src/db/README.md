### Change folder of video
```
modify \
  -i data/patches/Sept23-real/w55-e04.db \
  -o data/patches/Sept23-real/w55-e04.db \
  moveVideo \
    --image_video data/patches/Sept23-real/w55-e04 \
    --mask_video data/patches/Sept23-real/w55-e04mask
```

# Labelme

### Export images for labelling
```
modify \
    -i data/patches/Sept23-real/w55-e04.db \
    exportImagesToFolder --image_dir ~/src/labelme/LabelMeAnnotationTool/Images/w55-e04
```

### Export cars for labelling
```
# Only good types.
modify \
    -i data/databases/wpitch.db \
    filterUnknownNames \
    filterCustom --car_constraint "width > 55 AND height > 55 AND name IN ('van', 'taxi', 'sedan')" \
    filterByIntersection --intersection_thresh_perc 0.2 \
    expandBoxes --expand_perc 0.2 \
    filterByBorder \
    exportCarsToDataset --edges distort --target_width 64 --target_height 64 --patch_db_file data/patches/Oct10-real/w55-goodtypes-e04.db \
    deleteEmptyImages

# All types.
modify \
    -i data/databases/wpitch.db \
    filterUnknownNames \
    filterByIntersection --intersection_thresh_perc 0.2 \
    expandBoxes --expand_perc 0.2 \
    filterByBorder \
    exportCarsToDataset --edges distort --target_width 64 --target_height 64 --patch_db_file data/patches/Sept23-real/w55-e04.db \
    deleteEmptyImages
```

### Import labelme car annotations
```
name=ecyuo
modify \
    -i data/patches/Sept23-real/w55-e04.db \
    -o data/patches/Sept23-real/w55-e04-${name}.db \
   importLabelmeCars --in_annotations_dir data/patches/Sept23-real/w55-e04-${name} \
   polygonsToMasks --mask_name w55-e04mask-${name=ecyuo}.avi --write_null_mask_entries
```

### Merge polygons from different dbs
```
modify \
  -i data/patches/Sept23-real/w55-e04-sngandhi.db \
  -o data/patches/Sept23-real/w55-e04mask.db \
  mergePolygonsIntoMask \
    --add_db_files \
      data/patches/Sept23-real/w55-e04-ecyou.db \
      data/patches/Sept23-real/w55-e04-mhsieh2.db \
      data/patches/Sept23-real/w55-e04-ylp.db \
    --out_mask_video_file data/patches/Sept23-real/w55-e04mask.avi
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

