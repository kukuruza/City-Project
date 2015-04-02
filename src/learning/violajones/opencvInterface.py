import logging
import sys
import os, os.path as op
import shutil
import glob
import json
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import subprocess



class ExperimentsBuilder:
    def getResult (self):
        return self.experiments
    def __init__ (self, mine, parent = {}):
        filt = dict((k,v) for k, v in mine.iteritems() if k != '__children__')
        merged = dict(parent.items() + filt.items())
        if '__children__' in mine.keys():
            self.experiments = []
            for child in mine['__children__']:
                self.experiments += ExperimentsBuilder(child, merged).getResult()
        else:
            self.experiments = [merged]


def loadJson (json_path):
    json_path = op.join(os.getenv('CITY_DATA_PATH'), json_path)
    if not op.exists(json_path):
        raise Exception('json_path does not exist: ' + json_path)
    json_file = open(json_path)
    json_dict = json.load(json_file)
    json_file.close()
    return json_dict


def execCommand (command, logpath, wait = True):
    command = ' '.join(command)
    logging.info ('command: ' + command)
    with open(logpath, 'w') as logfile:

        p = subprocess.Popen(
            command, 
            shell=True, 
            universal_newlines=True, 
            stdout=logfile,
            stderr=subprocess.STDOUT)
        if wait:
            ret_code = p.wait()
            if ret_code != 0: 
                logging.error(ret_code)
                sys.exit()
            logfile.flush()
        logging.debug('finished run()')



