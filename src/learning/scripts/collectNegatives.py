import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import negatives


setupLogging ('log/learning/collectNegatives.log', logging.INFO, 'a')

db_path      = 'datasets/labelme/Databases/572/filt-frames.db'
out_dir      = 'clustering/negatives/neg-dense-frames/mask-adaptive/di0.2-er0.3-bl2-noise1.5'

params = { 'method': 'mask',
           'dilate': 0.2,
           'erode': 0.3,
           'debug_show': False,
           'noise_level': 1.5,
           'pixelation': 4,
           'blur_sigma': 2,
           'sizemap_path': 'models/cam572/sizeMap.tiff'
         }
negatives.negativeGrayspots (db_path, out_dir, params)

#in_dir = 'clustering/negatives/sparse-masked/negatives_for_all'
#out_dir = 'clustering/negatives/neg-sparse-patches/masked-24x18'
#params = { 'size_map_path': 'models/cam572/sizeMap.tiff',
#           'resize': [24, 18],
#           'number': 1000,
#           'minwidth': 50,
#           'maxwidtdh': 100,
#           'max_masked_perc': 0.3,
#         }
#negatives.negativeImages2patches (in_dir, out_dir, params)

#negatives.negativePatchesViaMaskfiles (db_path, filters_path, out_dir, params)
