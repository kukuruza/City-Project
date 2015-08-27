import logging
import os, sys
sys.path.insert(0, os.path.abspath('..'))
import helperSetup
import dbExport


helperSetup.setupLogging ('log/learning/mergeHdf5.log', logging.INFO, 'a')

# combine positive and negative into one hdf5 file
h5_in_path1 = 'clustering/negatives/572-Oct30-17h-pair/negatives-circle-noise-sc0.8-bl2.h5'
h5_in_path2 = 'clustering/sedan-e0.3/sedan-40x30.h5'
h5_out_path = 'clustering/sedan-e0.3/sedan-negatives5000-40x30.h5'
dbExport.mergeHDF5 (h5_in_path1, h5_in_path2, h5_out_path)
