import logging
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import helperSetup
import dbModify


helperSetup.setupLogging ('log/learning/Manually.log', logging.INFO, 'a')

db_vj_distant = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected-vj-distant/mhr0.995-mfar0.7-wtr0.95.db'
db_vj_close   = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected-vj-close/mhr0.995-mfar0.7-wtr0.95.db'
db_fromback   = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected/fromback-dr8.db'
db_out_path   = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected/all-3.db'

(conn, cursor) = helperSetup.dbInit(db_fromback, db_fromback + '-tmp')
dbModify.maskScores (cursor, {'score_map_path': 'models/cam572/mapFromback.tiff'})
conn.commit()
conn.close()

(conn, cursor) = helperSetup.dbInit(db_vj_distant, db_vj_distant + '-tmp')
dbModify.maskScores (cursor, {'score_map_path': 'models/cam572/mapVjDistant-nhor.tiff'})
conn.commit()
conn.close()

(conn, cursor) = helperSetup.dbInit(db_vj_distant + '-tmp', db_out_path)
dbModify.merge (cursor, db_fromback + '-tmp')
dbModify.merge (cursor, db_vj_close)
dbModify.filterSize (cursor, {'size_map_path': 'models/cam572/mapSize.tiff', 'debug_show': False } )
dbModify.thresholdScore (cursor, {'threshold': 0.7, 'debug_show': False } )
dbModify.clusterBboxes (cursor, {'threshold': 0.7, 'debug_show': False})\
dbManual.show(cursor)
conn.commit()
conn.close()



