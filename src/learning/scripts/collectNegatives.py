import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
from setupHelper import setupLogging
import negatives


setupLogging ('log/learning/collectNegatives.log', logging.INFO, 'a')

db_path      = 'datasets/labelme/Databases/572/filt-frames.db'
out_dir      = 'clustering/negatives/neg-dense-frames/mask-params/di0.3-er0.4'

params = { 'spot_scale': 0.7,
           'method': 'mask',
           'dilate': 0.3,
           'erode': 0.4,
           'debug_show': False,
           'width': 24 }
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

#negatives.negativeViaMaskfiles (db_path, filters_path, out_dir, params)
