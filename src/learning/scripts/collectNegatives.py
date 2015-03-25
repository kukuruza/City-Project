import logging
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from utilities import setupLogging
import negatives


setupLogging ('log/learning/collectNegatives.log', logging.INFO, 'a')

db_path      = 'datasets/labelme/Databases/src-frames.db'
filters_path = 'clustering/filters/neg_24x18_car.json'
out_dir      = 'clustering/negatives/neg_car_masked'

#params = { 'spot_scale': 0.7,
#           'method': 'mask',
#           'dilate': 0.25,
#           'erode': 0.4 }
#negatives.negativeGrayspots (db_path, filters_path, out_dir, params)

in_dir = 'clustering/negatives/sparse_circle/negatives_for_all'
out_dir = 'clustering/negatives/sparse_patches_circle'
params = { 'resize': [40, 30] }
negatives.getNegativePatches (in_dir, out_dir, params)
