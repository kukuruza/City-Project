import numpy as np
import cv2
import os, sys
import os.path as op
import logging
from dbInterface import deleteCar, queryField
import dbInterface
from utilities import bbox2roi, roi2bbox, drawRoi, drawScoredRoi
import utilities
import ConfigParser  # for keys
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



# helper global vars for mouse callback
xpress, ypress = None, None
mousePressed = False
mouseReleased = False

# mouse callback for labelling matches
def monitorPressRelease (event,x,y,flags,param):
    global xpress, ypress, mousePressed, mouseReleased

    if event == cv2.EVENT_LBUTTONDOWN:
        xpress, ypress = x, y
        assert not mouseReleased
        mousePressed = True

    elif event == cv2.EVENT_LBUTTONUP:
        xpress, ypress = x, y
        assert not mousePressed
        mouseReleased = True




class ManualProcessor (BaseProcessor):

    def show (self, params = {}):
        logging.info ('==== show ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'disp_scale', 1.0)
        params = self.setParamUnlessThere (params, 'threshold_score', 0)
        image_constraint = ' WHERE ' + params['image_constraint'] if 'image_constraint' in params.keys() else ''
        car_constraint = ' AND (' + params['car_constraint'] + ')' if 'car_constraint' in params.keys() else ''

        c.execute('SELECT imagefile FROM images' + image_constraint)
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

                drawScoredRoi (img, roi, '', score)

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

        car_constraint = ' AND (' + params['car_constraint'] + ')' if 'car_constraint' in params.keys() else ''

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

                # draw image
                disp_scale = params['disp_scale']
                img_show = cv2.resize(img_show, (0,0), fx=disp_scale, fy=disp_scale)
                cv2.imshow('show', img_show)
                button = cv2.waitKey(-1)

                # checking button inside iterating cars
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

            # checking button inside iterating images (after exit from inner loop)
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



    def __drawMatch__ (self, img, roi1, roi2):
        offsetY = img.shape[0] / 2;
        #numpy.random.randint
        color = (0, 255, 0)
        roi2[0] += offsetY
        roi2[2] += offsetY
        drawRoi (img, roi1, None, color)
        drawRoi (img, roi2, None, color)
        center1 = utilities.getOpencvCenter(roi1)
        center2 = utilities.getOpencvCenter(roi2)
        cv2.line(img, center1, center2, color)


    def __findPressedCar__ (self, x, y, cars):
        for i in range(len(cars)):
            roi = queryField(cars[i], 'roi')
            if x >= roi[1] and x < roi[3] and y >= roi[0] and y < roi[2]:
                return i
        return None 


    def labelMatches (self, params = {}):
        logging.info ('==== labelMatches ====')
        c = self.cursor

        params = self.setParamUnlessThere (params, 'debug', False)
        params = self.setParamUnlessThere (params, 'disp_scale', 1.5)

        keys_config = self.__loadKeys__ (params)

        dbInterface.createTableMatches(c)

        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()
        logging.debug ('found %d images' % len(image_entries))

        if 'imagefile_start' in params.keys(): 
            imagefile_start = params['imagefile_start']
            try:
                index_im = image_entries.index((imagefile_start,))
                if index_im == 0:
                    index_im = 1
                    logging.warning ('can\'t start from image 0')
                logging.info ('starting from image %d' % index_im)
            except ValueError:
                logging.error ('provided image does not exist ' + imagefile_start)
                sys.exit()
        else:
            index_im = 1

        # set up callback
        cv2.namedWindow('show')
        cv2.setMouseCallback('show', monitorPressRelease)
        global mousePressed, mouseReleased, xpress, ypress

        button = -1
        while button != 27 and index_im < len(image_entries):
            (imagefile1,) = image_entries[index_im - 1]
            (imagefile2,) = image_entries[index_im]
        
            # load the image pair
            imagepath1 = op.join (os.getenv('CITY_DATA_PATH'), imagefile1)
            if not op.exists (imagepath1):
                raise Exception ('image does not exist: ' + imagepath1)
            img1 = cv2.imread(imagepath1)
            imagepath2 = op.join (os.getenv('CITY_DATA_PATH'), imagefile2)
            if not op.exists (imagepath2):
                raise Exception ('image does not exist: ' + imagepath2)
            img2 = cv2.imread(imagepath2)
            # offset of the 2nd image, when they are stacked
            yoffset = img1.shape[0]

            # get cars from both images
            c.execute('SELECT * FROM cars WHERE imagefile=? ', (imagefile1,))
            cars1 = c.fetchall()
            logging.info ('%d cars found for %s' % (len(cars1), imagefile1))
            c.execute('SELECT * FROM cars WHERE imagefile=? ', (imagefile2,))
            cars2 = c.fetchall()
            logging.info ('%d cars found for %s' % (len(cars2), imagefile2))

            # draw cars in both images
            for car in cars1:
                roi = queryField(car, 'roi')
                drawRoi (img1, roi)
            for car in cars2:
                roi = queryField(car, 'roi')
                drawRoi (img2, roi)

            i1 = i2 = None

            # each cycle is some some key is pressed
            #   fortunately all the keys mean some serious update
            button = -1
            while button == -1:

                img_stack = np.vstack((img1, img2))

                if i1 is None and i2 is None:

                    # find existing matches
                    for car1 in cars1:
                        for car2 in cars2:
                            s = '''SELECT match FROM matches WHERE carid = ?
                                   INTERSECT
                                   SELECT match FROM matches WHERE carid = ?'''
                            c.execute(s, (queryField(car1, 'id'), queryField(car2, 'id')))
                            if c.fetchone() is not None:
                                roi1 = queryField(car1, 'roi')
                                roi2 = queryField(car2, 'roi')
                                self.__drawMatch__ (img_stack, roi1, roi2)

                    # draw image
                    disp_scale = params['disp_scale'] / 2
                    img_show = cv2.resize(img_stack, (0,0), fx=disp_scale, fy=disp_scale)
                    cv2.imshow('show', img_show)

                # process mouse callback effect (button has been pressed)
                if mousePressed:
                    i2 = None  # reset after the last
                    logging.debug ('pressed  x=%d, y=%d' % (xpress, ypress))
                    xpress /= disp_scale
                    ypress /= disp_scale
                    i1 = self.__findPressedCar__ (xpress, ypress, cars1)
                    if i1 is not None: logging.debug ('found pressed car number: %d' % i1)
                    mousePressed = False

                # process mouse callback effect (button has been released)
                if mouseReleased:
                    logging.debug ('released x=%d, y=%d' % (xpress, ypress))
                    xpress /= disp_scale
                    ypress /= disp_scale
                    i2 = self.__findPressedCar__ (xpress, ypress - yoffset, cars2)
                    if i2 is not None: logging.debug ('found released car number: %d' % i2)
                    mouseReleased = False

                # if we could find pressed and released cars, add match
                if i1 is not None and i2 is not None:

                    # add the match to the list
                    carid1 = queryField(cars1[i1], 'id')
                    carid2 = queryField(cars2[i2], 'id')
                    logging.info ('detected a match')

                    # find a free match index
                    c.execute('SELECT MAX(match) FROM matches')
                    match = int(c.fetchone()[0]) + 1

                    c.execute('INSERT INTO matches(match, carid) VALUES (?,?)', (match, carid1))
                    c.execute('INSERT INTO matches(match, carid) VALUES (?,?)', (match, carid2))

                    # display the match
                    roi1 = queryField(cars1[i1], 'roi')
                    roi2 = queryField(cars2[i2], 'roi')
                    roi2[0] += yoffset
                    roi2[1] += yoffset
                    self.__drawMatch__ (img_stack, roi1, roi2)

                    # reset
                    i1 = i2 = None

                # stay inside the loop inside one image pair until some button is pressed
                button = cv2.waitKey(50)

            if button == keys_config['left']:
                logging.debug ('prev image pair')
                if index_im == 1:
                    print ('already the first image pair')
                else:
                    index_im -= 1
            elif button == keys_config['right']:
                logging.debug ('next image pair')
                index_im += 1  # exit at last image pair from outer loop

        return self


