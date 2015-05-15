import os, sys
import logging
import os.path as op
import glob
import shutil
import sqlite3



class BaseProcessor:

    def __init__ (self, db_in_path, db_out_path = None):

        if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
            raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH')

        logging.info ('db_in_path:  ' + str(db_in_path))
        logging.info ('db_out_path: ' + str(db_out_path))

        self.CITY_DATA_PATH = os.environ.get('CITY_DATA_PATH')
        db_in_path   = op.join (self.CITY_DATA_PATH, db_in_path)
        db_out_path  = op.join (self.CITY_DATA_PATH, db_out_path) if db_out_path else db_in_path

        self.__setupCopyDb__ (db_in_path, db_out_path)

        self.conn = sqlite3.connect (db_out_path)
        self.cursor = self.conn.cursor()


    def commit (self):
        self.conn.commit()
        self.conn.close()


    def forget (self):
        self.conn.close()



    def __setupCopyDb__ (self, db_in_path, db_out_path):
        if not op.exists (db_in_path):
            raise Exception ('db does not exist: ' + db_in_path)
        if op.exists (db_out_path):
            logging.warning ('will back up existing db_out_path')
            backup_path = db_out_path + '.backup'
            if db_in_path != db_out_path:
                if op.exists (backup_path): os.remove (backup_path)
                os.rename (db_out_path, backup_path)
            else:
                shutil.copyfile(db_in_path, backup_path)
        if db_in_path != db_out_path:
            shutil.copyfile(db_in_path, db_out_path)


    def setParamUnlessThere (self, params, key, default_value):
        if not key in params.keys(): params[key] = default_value
        return params

    def verifyParamThere (self, params, key):
        if not key in params.keys():
            raise Exception ('"' + key + '" not found in params')
        return params



