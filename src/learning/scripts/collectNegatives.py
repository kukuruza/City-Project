import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import negatives


setupLogging ('log/learning/CollectNegatives.log', logging.INFO, 'a')

#db_path      = 'datasets/labelme/Databases/572/filt-frames.db'
#out_dir      = 'clustering/negatives/neg-dense-frames/circle-noise/sc0.8-bl2'
#params = { 'method': 'circle',
#           'spot_scale': 0.8,
#           'dilate': 0.2,
#           'erode': 0.3,
#           'debug_show': False,
#           'noise_level': 0,
#           'pixelation': 4,
#           'blur_sigma': 2,
#           'sizemap_path': 'models/cam572/mapSize.tiff'
#         }
#negatives.negativeGrayspots (db_path, out_dir, params)

in_dir = 'clustering/negatives/neg-dense-frames/mask-noise-crop/noise1.5-pxl5'
out_dir = 'clustering/negatives/neg-dense-patches/masked-24x18-many'
params = { 'size_map_path': 'models/cam572/mapSize.tiff',
           'resize': [24, 18],
           'number': 2000,
           'minwidth': 50,
           'maxwidth': 100,
           'max_masked_perc': 0.3,
         }
negatives.negativeImages2patches (in_dir, out_dir, params)
