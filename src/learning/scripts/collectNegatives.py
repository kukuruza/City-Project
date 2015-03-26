import logging
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from utilities import setupLogging
import negatives


setupLogging ('log/learning/collectNegatives.log', logging.INFO, 'a')

db_path      = 'datasets/labelme/Databases/src-frames.db'
filters_path = 'clustering/filters/neg_24x18_car.json'
#out_dir      = 'clustering/negatives/neg_car_masked'

#params = { 'spot_scale': 0.7,
#           'method': 'mask',
#           'dilate': 0.25,
#           'erode': 0.4 }
#negatives.negativeGrayspots (db_path, filters_path, out_dir, params)

#in_dir = 'clustering/negatives/sparse-masked/negatives_for_all'
out_dir = 'clustering/negatives/neg-sparse-patches/masked-24x18'
params = { 'size_map_path': 'models/cam572/sizeMap.tiff',
           'resize': [24, 18],
           'number': 1000,
           'minwidth': 50,
           'maxwidtdh': 100,
           'max_masked_perc': 0.3,
         }
#negatives.negativeImages2patches (in_dir, out_dir, params)

negatives.negativeViaMaskfiles (db_path, filters_path, out_dir, params)
