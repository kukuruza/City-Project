import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbNegatives import negativeGrayspots, fillNegativeDbWithBboxes
from learning.dbExport    import collectGhostsHDF5

'''
Populate negative db with negative bboxes.

Motivation: since commit #d546455 we use hdf5 instead directories of patches.
  See issue #28 for further information.
  Negatives had to move to hdf5 too. We moved to intermediate .db files because:
  1) necessity to move
  2) general preference of db interfaces
  3) can use collectGhostPatches function in negatives too (avoid code duplication)

This is the former pipeline to extract the negatives:
  1) Write negative frames with 'grayspots' 
  2) Extract negative patches, and save as images in a directory

This is the new pipeline to extract the negatives:
  1) Write negative frames with 'grayspots' and a .db with new ghostfiles (negativeGrayspots)
  2) Populate with bboxes (fillNegativeDbWithBboxes)
  3) Extract negative patches, and save as hdf5 (exporting.collectGhostsHDF5)
'''

setupLogging ('log/learning/CollectNegatives.log', logging.DEBUG, 'a')

# NOT used
# video_in_file = 'camdata/cam541/Jul26-16h-ghost.avi'
# h5_out_file = 'clustering/unlabelled/Jul26-16h-40x30.h5'
# params = { 'size_map_path': 'models/cam572/mapSize.tiff',
#            'number': 100,
#            'resize': [40, 30],
#            'minwidth': 15,
#            'maxwidth':  100,
#            'write_samples': 5
#          }
# dbNegatives.collectRandomPatchesFromVideoHDF5 (video_in_file, h5_out_file, params)


# step 1: write negative frames with 'grayspots'
db_in_file   = 'databases/labelme/572-Oct30-17h-frame/parsed.db'
out_dir      = 'patches/negatives/test'
params = { 'method': 'circle',
           'spot_scale': 0.8,
           'dilate': 0.2,
           'erode': 0.3,
           'debug_show': False,
           'noise_level': 0,
           'pixelation': 4,
           'blur_sigma': 2,
           'sizemap_path': 'models/cam572/mapSize.tiff'
         }
db_neg_file = 'patches/negatives/test/negatives-circle-noise-sc0.8-bl2.db'
(conn, cursor) = dbInit(db_in_file, db_neg_file)
negativeGrayspots (cursor, out_dir, params)
conn.commit()
conn.close()

# step 2: populate with bboxes
params = { 'size_map_path': 'models/cam572/mapSize.tiff',
           'resize': [24, 18],
           'number': 2000,
           'minwidth': 50,
           'maxwidth': 100,
           'max_masked_perc': 0.3,
         }
db_filled_file = 'patches/negatives/test/negatives-circle-noise-sc0.8-bl2-filled.db'
(conn, cursor) = dbInit(db_neg_file, db_filled_file)
fillNegativeDbWithBboxes (cursor, params)
conn.commit()
conn.close()

# step 3: extract negative patches, and save as hdf5
hdf5_out_file = 'patches/negatives/test/negatives-circle-noise-sc0.8-bl2.h5'
params = { 'resize': [40, 30], 
           'label': 0
         }
collectGhostsHDF5 (db_filled_file, hdf5_out_file, params)



