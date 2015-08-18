import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
import helperSetup
import dbExport


helperSetup.setupLogging ('log/learning/writeInfoFile.log', logging.INFO, 'a')

in_db_path   = 'datasets/labelme/Databases/distinct-frames.db'
filters_path = 'clustering/filters/all.json'
out_dir      = 'learning/violajones/ground_truth'
dbExport.writeInfoFile (in_db_path, filters_path, out_dir)

#dir_in = 'exporting/name-sparse-e0.1/car-24x18/'
#dat_out_path = 'learning/violajones/positives/tests/test_24x18.dat'
#dbExport.patches2datFile (dir_in, dat_out_path)

