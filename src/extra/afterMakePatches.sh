src/db/convert.py -i data/patches/Nov05-size600-90turn/scenes.db filterCustom --car_constraint "width > 80 AND height > 80 AND score > 0.8" expandBoxes --expand_perc 0.2 filterByBorder exportCarsToDataset --patch_db_file data/patches/data/patches/Nov05-size600-90turn/w256-e02-distort.db --target_width 256 --target_height 256 --edge distort

