import logging
import os, sys, os.path as op
import re
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../../learning'))
import helperSetup
import dbExport
import DeploymentPatches


helperSetup.setupLogging ('log/cnn/PredictH5.log', logging.INFO, 'a')

network_path = 'cnn/architectures/sedan-h5-features-py.prototxt'
model_path   = 'cnn/models/sedan-h5_iter_4000.caffemodel'
deployment = DeploymentPatches.DeploymentPatches (network_path, model_path)

patch_helper = dbExport.PatchHelperHDF5()
patch_helper.initDataset ('patches/try-hdf5/testing-40x30')

with open(op.join(os.getenv('CITY_DATA_PATH'), 'patches/try-hdf5/features-ip2-py.txt'), 'w') as f:
    while True:
        try:
            (patch, carid, label) = patch_helper.readPatch()
        except:
            break

        features = deployment.forward(patch).tolist()
        f.write ('%s\n' % ' '.join(['%06f' % x for x in features]))


patch_helper.closeDataset ()
