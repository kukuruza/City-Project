import numpy as np
import cv2
import os, sys
import os.path as op
import logging
from dbInterface import deleteCar, queryField
from utilities import bbox2roi, roi2bbox, drawRoi
import ConfigParser              # for keys
import matplotlib.pyplot as plt  # for colormaps
from dbBase import BaseProcessor



def getCalibration ():
    CITY_PATH = os.environ.get('CITY_PATH')
    if not op.exists (op.join(CITY_PATH, 'etc')):
        os.mkdir (op.join(CITY_PATH, 'etc'))
    config_path = op.join(CITY_PATH, 'etc', 'config.ini')
    config = ConfigParser.ConfigParser()
    if op.exists (config_path):
        config.read(config_path)
        try:
           keys_dict = {}
           keys_dict['del']   = int(config.get('opencv_keys', 'del'))
           keys_dict['right'] = int(config.get('opencv_keys', 'right'))
           keys_dict['left']  = int(config.get('opencv_keys', 'left'))
           return keys_dict
        except:
           logging.info ('will calibrate the keys')
    cv2.imshow('dummy', np.zeros((10,10), dtype=np.uint8))
    config.add_section('opencv_keys')
    print ('please click on the opencv window and click "del"')
    keyd = cv2.waitKey(-1)
    config.set('opencv_keys', 'del', keyd)
    print ('please click on the opencv window and click "right arrow"')
    keyr = cv2.waitKey(-1)
    config.set('opencv_keys', 'right', keyr)
    print ('please click on the opencv window and click "left arrow"')
    keyl = cv2.waitKey(-1)
    config.set('opencv_keys', 'left', keyl)
    with open(config_path, 'a') as configfile:
        config.write(configfile)
    return { 'del': keyd, 'right': keyr, 'left': keyl }




class ManualProcessor (BaseProcessor):

    def show (self, params = {}):
        logging.info ('==== show ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'disp_scale', 1.5)
        params = self.setParamUnlessThere (params, 'threshold_score', 0)

        if 'car_constraint' in params.keys(): 
            car_constraint = ' AND (' + params['car_constraint'] + ')'
        else:
            car_constraint = ''

        c.execute('SELECT imagefile FROM images')
        imagefiles = c.fetchall()

        for (imagefile,) in imagefiles:

            imagepath = op.join (self.CITY_DATA_PATH, imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            img = cv2.imread(imagepath)

            c.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            for car_entry in car_entries:
                carid     = queryField(car_entry, 'id')
                roi       = bbox2roi (queryField(car_entry, 'bbox'))
                score     = queryField(car_entry, 'score')
                #name      = queryField(car_entry, 'name')

                logging.debug ('roi ' + str(roi) + ', score: ' + str(score))

                if score is None: score = 1

                if score < params['threshold_score']: continue

                color = tuple([int(x * 255) for x in plt.cm.jet(score * 255)][0:3])
                drawRoi (img, roi, '', color)

            disp_scale = params['disp_scale']
            img = cv2.resize(img, (0,0), fx=disp_scale, fy=disp_scale)
            cv2.imshow('show', img)
            if cv2.waitKey(-1) == 27: break

        cv2.destroyWindow('show')
        return self



    def __loadKeys__ (self, params):
        if 'keys_config' in params.keys() and 'calibrate' not in params.keys(): 
            keys_config = params['keys_config']
        else:
            keys_config = getCalibration()
        logging.info ('left:  ' + str(keys_config['left']))
        logging.info ('right: ' + str(keys_config['right']))
        logging.info ('del:   ' + str(keys_config['del']))
        return keys_config



    def examine (self, params = {}):
        logging.info ('==== examine ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'disp_scale', 1.5)

        color_config = {}
        color_config['']       = None
        color_config['black']  = (0,0,0)
        color_config['white']  = (255,255,255)
        color_config['blue']   = (255,0,0)
        color_config['yellow'] = (0,255,255)
        color_config['red']    = (0,0,255)
        color_config['green']  = (0,255,0)
        color_config['gray']   = (128,128,128)
        color_config['badroi'] = color_config['red']

        keys_config = self.__loadKeys__ (params)

        if 'car_constraint' in params.keys(): 
            car_constraint = ' AND (' + params['car_constraint'] + ')'
        else:
            car_constraint = ''

        c.execute('SELECT count(*) FROM cars WHERE 1' + car_constraint)
        (total_num,) = c.fetchone()
        logging.info('total number of objects found in db: ' + str(total_num))

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()

        if 'imagefile_start' in params.keys(): 
            imagefile_start = params['imagefile_start']
            try:
                index_im = image_entries.index((imagefile_start,))
            except ValueError:
                logging.error ('provided image does not exist ' + imagefile_start)
                sys.exit()
        else:
            index_im = 0

        car_statuses = {}
        button = 0
        index_car = 0
        while button != 27 and index_im < len(image_entries):
            (imagefile,) = image_entries[index_im]

            imagepath = op.join (self.CITY_DATA_PATH, imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            img = cv2.imread(imagepath)

            c.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
            else: index_car = 0
            while button != 27 and index_car >= 0 and index_car < len(car_entries):
                car_entry = car_entries[index_car]
                carid     = queryField(car_entry, 'id')
                roi       = bbox2roi (queryField(car_entry, 'bbox'))
                imagefile = queryField(car_entry, 'imagefile')
                name      = queryField(car_entry, 'name')
                color     = queryField(car_entry, 'color')

                # TODO: color based on score

                img_show = img.copy()
                drawRoi (img_show, roi, name, color_config[color or ''])

                disp_scale = params['disp_scale']
                img_show = cv2.resize(img_show, (0,0), fx=disp_scale, fy=disp_scale)
                cv2.imshow('show', img_show)
                button = cv2.waitKey(-1)

                if button == keys_config['left']:
                    logging.debug ('prev')
                    index_car -= 1
                elif button == keys_config['right']:
                    logging.debug ('next')
                    index_car += 1

            if button == keys_config['left']:
                logging.debug ('prev image')
                if index_im == 0:
                    print ('already the first image')
                else:
                    index_im -= 1
                    index_car = -1
            else: 
                logging.debug ('next image')
                index_im += 1

        cv2.destroyWindow('show')
        return self



    def classifyName (self, params = {}):
        logging.info ('==== classifyName ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'disp_scale', 1.5)

        keys_config = self.__loadKeys__ (params)

        keys_config[ord(' ')] = 'vehicle'    # but can't see the type, or not in the list
        keys_config[ord('s')] = 'sedan'      # generic small car
        keys_config[ord('d')] = 'double'     # several cars stacked into one bbox
        keys_config[ord('c')] = 'taxi'       # (cab)
        keys_config[ord('t')] = 'truck'
        keys_config[ord('v')] = 'van'        # (== a small truck)
        keys_config[ord('m')] = 'minivan'
        keys_config[ord('b')] = 'bus'
        keys_config[ord('p')] = 'pickup'
        keys_config[ord('l')] = 'limo'
        keys_config[ord('o')] = 'object'     # not a car, pedestrian, or bike
        keys_config[ord('h')] = 'pedestrian' # (human)
        keys_config[ord('k')] = 'bike'       # (bike or motobike)

        if 'car_constraint' in params.keys(): 
            car_constraint = ' AND (' + params['car_constraint'] + ')'
        else:
            car_constraint = ''

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()
        if 'imagefile_start' in params.keys(): 
            imagefile_start = params['imagefile_start']
            try:
                index_im = image_entries.index((imagefile_start,))
                logging.info ('starting from image ' + str(index_im))
            except ValueError:
                logging.error ('provided image does not exist ' + imagefile_start)
                sys.exit()
        else:
            index_im = 0

        c.execute('SELECT imagefile, ghostfile FROM images')
        image_entries = c.fetchall()

        car_statuses = {}
        button = 0
        index_car = 0
        while button != 27 and index_im < len(image_entries):
            (imagefile, ghostfile) = image_entries[index_im]

            ghostpath = op.join (self.CITY_DATA_PATH, ghostfile)
            if not op.exists (ghostpath):
                raise Exception ('image does not exist: ' + ghostpath)
            ghost = cv2.imread(ghostpath)

            c.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
            else: index_car = 0
            while button != 27 and index_car >= 0 and index_car < len(car_entries):
                car_entry = car_entries[index_car]
                carid = queryField(car_entry, 'id')
                roi = bbox2roi (queryField(car_entry, 'bbox'))
                imagefile = queryField(car_entry, 'imagefile')

                # assign label for display
                if carid in car_statuses.keys():
                    label = car_statuses[carid]
                else:
                    label = queryField(car_entry, 'name')
                    if label == 'object': label = ''
                logging.debug ('label: "' + (label or '') + '"')

                img_show = ghost.copy()
                drawRoi (img_show, roi, label)

                disp_scale = params['disp_scale']
                img_show = cv2.resize(img_show, (0,0), fx=disp_scale, fy=disp_scale)
                cv2.imshow('show', img_show)
                button = cv2.waitKey(-1)

                if button == keys_config['left']:
                    logging.debug ('prev')
                    index_car -= 1
                elif button == keys_config['right']:
                    logging.debug ('next')
                    index_car += 1
                elif button == keys_config['del']:
                    logging.info ('delete')
                    car_statuses[carid] = 'badroi'
                    index_car += 1
                elif button in keys_config.keys():
                    logging.info (keys_config[button])
                    car_statuses[carid] = keys_config[button]
                    index_car += 1

            if button == keys_config['left']:
                logging.debug ('prev image')
                if index_im == 0:
                    print ('already the first image')
                else:
                    index_im -= 1
                    index_car = -1
            else: 
                logging.debug ('next image')
                index_im += 1

        cv2.destroyWindow('debug_show')

        # actually delete or update
        for (carid, status) in car_statuses.iteritems():
            if status == 'badroi':
                deleteCar (c, carid)
            elif status == '':
                c  # nothing
            else:
                c.execute('UPDATE cars SET name=? WHERE id=?', (status, carid))

        return self



    def classifyColor (self, params = {}):
        logging.info ('==== classifyColor ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'disp_scale', 1.5)

        keys_config = self.__loadKeys__ (params)

        keys_config[ord(' ')] = ''
        keys_config[ord('k')] = 'black'
        keys_config[ord('w')] = 'white'
        keys_config[ord('b')] = 'blue'
        keys_config[ord('y')] = 'yellow'
        keys_config[ord('r')] = 'red'
        keys_config[ord('g')] = 'green'
        keys_config[ord('s')] = 'gray'

        color_config = {}
        color_config['']       = None
        color_config['black']  = (0,0,0)
        color_config['white']  = (255,255,255)
        color_config['blue']   = (255,0,0)
        color_config['yellow'] = (0,255,255)
        color_config['red']    = (0,0,255)
        color_config['green']  = (0,255,0)
        color_config['gray']   = (128,128,128)
        color_config['badroi'] = color_config['red']

        if 'car_constraint' in params.keys(): 
            car_constraint = ' AND (' + params['car_constraint'] + ')'
        else:
            car_constraint = ''

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()

        if 'imagefile_start' in params.keys(): 
            imagefile_start = params['imagefile_start']
            try:
                index_im = image_entries.index((imagefile_start,))
                logging.info ('starting from image ' + str(index_im))
            except ValueError:
                logging.error ('provided image does not exist ' + imagefile_start)
                sys.exit()
        else:
            index_im = 0

        car_statuses = {}
        button = 0
        index_car = 0
        while button != 27 and index_im < len(image_entries):
            (imagefile,) = image_entries[index_im]

            imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
            if not op.exists (imagepath):
                raise Exception ('image does not exist: ' + imagepath)
            img = cv2.imread(imagepath)

            c.execute('SELECT * FROM cars WHERE imagefile=? ' + car_constraint, (imagefile,))
            car_entries = c.fetchall()
            logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

            if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
            else: index_car = 0
            while button != 27 and index_car >= 0 and index_car < len(car_entries):
                car_entry = car_entries[index_car]
                carid     = queryField(car_entry, 'id')
                roi       = bbox2roi (queryField(car_entry, 'bbox'))
                imagefile = queryField(car_entry, 'imagefile')

                # assign label for display
                if carid in car_statuses.keys():
                    label = car_statuses[carid]
                else:
                    label = queryField(car_entry, 'color')
                logging.debug ('label: "' + (label or '') + '"')

                img_show = img.copy()
                drawRoi (img_show, roi, label, color_config[label or ''])

                disp_scale = params['disp_scale']
                img_show = cv2.resize(img_show, (0,0), fx=disp_scale, fy=disp_scale)
                cv2.imshow('show', img_show)
                button = cv2.waitKey(-1)

                if button == keys_config['left']:
                    logging.debug ('prev')
                    index_car -= 1
                elif button == keys_config['right']:
                    logging.debug ('next')
                    index_car += 1
                elif button == keys_config['del']:
                    logging.info ('delete')
                    car_statuses[carid] = 'badroi'
                    index_car += 1
                elif button in keys_config.keys():
                    logging.info (keys_config[button])
                    car_statuses[carid] = keys_config[button]
                    index_car += 1

            if button == keys_config['left']:
                logging.debug ('prev image')
                if index_im == 0:
                    print ('already the first image')
                else:
                    index_im -= 1
                    index_car = -1
            else: 
                logging.debug ('next image')
                index_im += 1

        cv2.destroyWindow('debug_show')

        # actually delete or update
        for (carid, status) in car_statuses.iteritems():
            if status == 'badroi':
                deleteCar (c, carid)
            elif status == '':
                c.execute('UPDATE cars SET color=? WHERE id=?', (None, carid))
            else:
                c.execute('UPDATE cars SET color=? WHERE id=?', (status, carid))

        return self

