import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import h5py
from learning.helperSetup import setupLogging, dbInit, atcity
from learning.dbExport    import collectPatches, writeReadme, PatchHelperFolder
from learning.helperH5    import viewPatches
from learning.dbModify    import filterCustom


setupLogging ('log/learning/ExportPatches.log', logging.INFO, 'a')

in_db_file  = 'databases/sparse/all-Feb29-wr-wb.db'
out_dataset = 'augmentation/patches/sparse-taxi'

#(conn, cursor) = dbInit(atcity(in_db_file))
#params = {'label': 1, 'resize': (40, 30), 'constraint': "name = 'sedan' AND width >= 30 AND width < 80"}
#collectPatches (cursor, out_dataset, params)
#conn.close()

#with h5py.File (atcity(out_dataset + '.h5')) as f:
#    helperH5.shuffle (f)
#    helperH5.multipleOf (f, 100)
#    viewPatches (f, {'random': True, 'scale': 4})



(conn, cursor) = dbInit(in_db_file)
filterCustom (cursor, params = {'car_constraint': 'name = "taxi" AND width >= 60'})
params = {'patch_helper': PatchHelperFolder(), 'resize': (80, 60)}
#params.update({'flip': True, 'blur': 0.25, 'color': 0, 'transl_perc': 0.1, 'scale': 0.05, 'rotate_deg': 5})
#writeReadme (in_db_file, out_dataset, params)
collectPatches (cursor, out_dataset, params)
conn.close()
