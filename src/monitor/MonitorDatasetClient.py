import sys, os, os.path as op
import logging
import argparse
import ConfigParser
from inspect import getframeinfo, stack
from datetime import datetime
import json
import urllib2, base64
import subprocess
from math import sqrt


def _sq_(x): return pow(x,2)

def _get_norm_wh_(a): return sqrt(_sq_(a['width']) + _sq_(a['height']))


class MonitorDatasetClient ():

    def _read_config_file_ (self, config_file, relpath):
        config_path = op.join(relpath, config_file)
        assert op.exists(config_path)

        # try to read keys from the file
        config = ConfigParser.ConfigParser()
        config.read(config_path)
        try:
           self.enabled            = bool(config.get('3dmodel_generate_frame', 'enable'))
           self.max_time           = float(config.get('3dmodel_generate_frame', 'max_time'))
           self.server_address     = config.get('3dmodel_generate_frame', 'server_address')
           self.server_credentials = config.get('3dmodel_generate_frame', 'server_credentials')
           self.machine_name       = config.get('3dmodel_generate_frame', 'machine_name')
           logging.info ('config enable:           %s' % str(self.enabled))
           logging.info ('config max time:         %f' % self.max_time)
           logging.info ('config server_address:   %s' % self.server_address)
           logging.info ('config machine_name:     %s' % self.machine_name)
        except:
           raise Exception ('MonitorAugmentationClient: cannot read config file.')


    def __init__ (self, cam_id, config_file='etc/monitor.ini',
                        cam_timezone='-05:00', relpath=os.getenv('CITY_PATH')):

        self.cam_id = cam_id
        self.cam_timezone = cam_timezone
        self.relpath = relpath
        #self.verbose = args.verbose

        self._read_config_file_ (config_file, self.relpath)


    def upload_vehicle (self, vehicle, timestamp=datetime.now()):
        
        if not self.enabled:
            logging.debug ('MonitorAugmentationClient not uploading -- disabled')
            return

        # get name of the program which called me
        caller = getframeinfo(stack()[1][0])
        logging.debug ('%s:%d' % (caller.filename, caller.lineno))

        # form json
        timestr = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + self.cam_timezone
        message = {'date':             timestr,
                   'machine_name':     self.machine_name,
                   'program_name':     op.basename(caller.filename),
                   'camera_id':        self.cam_id,
                   'camera_time_zone': self.cam_timezone,
                   'vehicle_type':     vehicle['vehicle_type'],
                   'yaw':              vehicle['yaw'],
                   'pitch':            vehicle['pitch'],
                   'pxl_size':         round(_get_norm_wh_(vehicle))
                  }
        logging.debug (json.dumps(message, indent=4))

        # only WITH credentials
        command = 'curl --connect-timeout %s -u %s -XPOST \'%s/datasets/vehicle/\' -d \'%s\'' % \
                  (self.max_time, self.server_credentials, \
                   self.server_address, json.dumps(message))
        logging.debug ('curl command: %s' % command)
        returncode = subprocess.call ([command], shell=True)
        logging.info ('MonitorAugmentation: curl returned code %s' % str(returncode))

        # TODO: get this working instead of calling curl above
        # # only WITH credentials
        # request = urllib2.Request (self.server_address+'/datasets/vehicle/', json.dumps(message), 
        #                           {'Content-Type': 'application/json'})
        # base64string = base64.encodestring(self.server_credentials)
        # request.add_header('Authorization', 'Basic %s' % base64string)   
        # f = urllib2.urlopen(request)
        # response = json.loads(f.read())
        # f.close()
        # print response


if __name__ == "__main__":
    logging.basicConfig (level=logging.DEBUG)
    monitor = MonitorDatasetClient (cam_id=572)
    monitor.upload_vehicle({'vehicle_type': 'taxi', 'yaw': 30, 'pitch': 50,
        'width': 20, 'height': 30})
    