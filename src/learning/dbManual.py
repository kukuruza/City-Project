import os, sys, os.path as op
import numpy as np
import cv2
import logging
import sqlite3
from dbUtilities import bbox2roi, roi2bbox, drawRoi, drawScoredRoi, getCenter
from helperDb    import deleteCar, carField, createTableMatches
from helperSetup import setParamUnlessThere
from helperKeys  import KeyReaderUser, getCalibration
from helperImg   import ReaderVideo



def getInfo (c, params = {}):
    '''Show major info of database. To be used when a db view is not available.
    Will add more options when he need comes.
    '''
    info = {}
    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()
    info['numimages'] = len(imagefiles)
    imagedirs = [op.dirname(x) for x, in imagefiles]
    imagedirs = list(set(imagedirs))
    info['imagedirs'] = imagedirs

    return info


def show (c, params = {}):
    '''
    Browse through database and see car bboxes on top of images. Colors are not shown.
    Any key will scroll to the next image.
    '''
    logging.info ('==== show ====')
    setParamUnlessThere (params, 'show_empty_frames', False)
    setParamUnlessThere (params, 'display_scale',     1.0)
    setParamUnlessThere (params, 'image_processor',   ReaderVideo())
    setParamUnlessThere (params, 'key_reader',        KeyReaderUser())
    setParamUnlessThere (params, 'shuffle',           False)

    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()

    if params['shuffle']:
      np.random.shuffle(imagefiles)

    for (imagefile,) in imagefiles:
        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info ('%d cars found for %s' % (len(car_entries), imagefile))

        if len(car_entries) == 0 and not params['show_empty_frames']:
            continue

        display = params['image_processor'].imread(imagefile)

        for car_entry in car_entries:
            roi       = bbox2roi (carField(car_entry, 'bbox'))
            score     = carField(car_entry, 'score')
            #name      = carField(car_entry, 'name')

            if score is None: score = 1
            logging.info ('roi: %s, score: %f' % (str(roi), score))
            drawScoredRoi (display, roi, '', score)

        f = params['display_scale']
        cv2.imshow('display', cv2.resize(display, (0,0), fx=f, fy=f))
        if params['key_reader'].readKey() == 27: break



def showPair (c, c_ref, params = {}):
    ''' Show side by side. Iterate c, c_ref should have same imagefiles. '''

    logging.info ('==== show ====')
    setParamUnlessThere (params, 'show_empty_frames', False)
    setParamUnlessThere (params, 'display_scale',     1.0)
    setParamUnlessThere (params, 'image_processor',   ReaderVideo())
    setParamUnlessThere (params, 'key_reader',        KeyReaderUser())
    setParamUnlessThere (params, 'shuffle',           False)

    c.execute('SELECT imagefile FROM images')
    imagefiles = c.fetchall()

    if params['shuffle']:
      np.random.shuffle(imagefiles)

    for (imagefile,) in imagefiles:
        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info ('%d cars found for %s' % (len(car_entries), imagefile))

        c_ref.execute('SELECT COUNT(*) FROM images WHERE imagefile=?', (imagefile,))
        assert len(c_ref.fetchone()) > 0, imagefile

        c_ref.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries_ref = c_ref.fetchall()
        logging.info ('%d cars found for %s' % (len(car_entries_ref), imagefile))

        if len(car_entries) == 0 and not params['show_empty_frames']:
            continue

        display = params['image_processor'].imread(imagefile)
        display_ref = display.copy()

        for car_entry in car_entries:
            roi       = bbox2roi (carField(car_entry, 'bbox'))
            score     = carField(car_entry, 'score')
            #name      = carField(car_entry, 'name')

            if score is None: score = 1
            logging.info ('roi: %s, score: %f' % (str(roi), score))
            drawScoredRoi (display, roi, '', score)

        for car_entry in car_entries_ref:
            roi       = bbox2roi (carField(car_entry, 'bbox'))
            score     = carField(car_entry, 'score')
            #name      = carField(car_entry, 'name')

            if score is None: score = 1
            logging.info ('roi: %s, score: %f' % (str(roi), score))
            drawScoredRoi (display_ref, roi, '', score)

        f = params['display_scale']
        display = cv2.resize(display, (0,0), fx=f, fy=f)
        display_ref = cv2.resize(display_ref, (0,0), fx=f, fy=f)
        cv2.imshow('display', np.hstack((display, display_ref)))
        if params['key_reader'].readKey() == 27: break



def examine (c, params = {}):
    '''
    Browse through database and see car bboxes on top of images. Colors are shown.
    Left/right key will loop through images.
    This is an enhanced version of show() function for careful examination.
    '''
    logging.info ('==== examine ====')
    setParamUnlessThere (params, 'disp_scale',       1.5)
    setParamUnlessThere (params, 'image_processor',  ReaderVideo())
    setParamUnlessThere (params, 'key_reader',       KeyReaderUser())
    keys = getCalibration()

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

    c.execute('SELECT count(*) FROM cars')
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

        img = None

        c.execute('SELECT * FROM cars WHERE imagefile=?', (imagefile,))
        car_entries = c.fetchall()
        logging.info ('%d cars found for %s' % (len(car_entries), imagefile))

        if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
        else: index_car = 0
        while button != 27 and index_car >= 0 and index_car < len(car_entries):
            car_entry = car_entries[index_car]
            roi       = bbox2roi (carField(car_entry, 'bbox'))
            imagefile = carField(car_entry, 'imagefile')
            name      = carField(car_entry, 'name')
            color     = carField(car_entry, 'color')

            # TODO: color based on score

            # lazily load image
            if img is None: img = params['image_processor'].imread(imagefile)

            display = img.copy()  # each car roi is drawn on a copy
            drawRoi (display, roi, name, color_config[color or ''])

            disp_scale = params['disp_scale']
            display = cv2.resize(display, (0,0), fx=disp_scale, fy=disp_scale)
            cv2.imshow('show', display)
            button = params['key_reader'].readKey()

            if button == keys['left']:
                logging.debug ('prev car')
                index_car -= 1
            elif button == keys['right']:
                logging.debug ('next car')
                index_car += 1

        if button == keys['left']:
            logging.debug ('prev image')
            if index_im == 0:
                logging.warning ('already the first image')
            else:
                index_im -= 1
                index_car = -1
        else: 
            logging.debug ('next image')
            index_im += 1



def classifyName (c, params = {}):
    '''
    Assign a name to each car (currently most names reflect car type)
    '''
    logging.info ('==== classifyName ====')
    setParamUnlessThere (params, 'disp_scale',       1.5)
    setParamUnlessThere (params, 'car_constraint',   '1')
    setParamUnlessThere (params, 'image_processor',  ReaderVideo())
    setParamUnlessThere (params, 'key_reader',       KeyReaderUser())
    keys = getCalibration()

    keys[ord(' ')] = 'vehicle'    # but can't see the type, or not in the list
    keys[ord('s')] = 'sedan'      # generic small car
    keys[ord('d')] = 'double'     # several cars stacked into one bbox
    keys[ord('c')] = 'taxi'       # (cab)
    keys[ord('t')] = 'truck'
    keys[ord('v')] = 'van'        # (== a small truck)
    keys[ord('m')] = 'minivan'
    keys[ord('b')] = 'bus'
    keys[ord('p')] = 'pickup'
    keys[ord('l')] = 'limo'
    keys[ord('o')] = 'object'     # not a car, pedestrian, or bike
    keys[ord('h')] = 'pedestrian' # (human)
    keys[ord('k')] = 'bike'       # (bike or motobike)

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

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    car_statuses = {}
    button = 0
    index_car = 0
    while button != 27 and index_im < len(image_entries):
        (imagefile,) = image_entries[index_im]

        image = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=? AND (%s)' % params['car_constraint'], (imagefile,))
        car_entries = c.fetchall()
        logging.info ('%d cars found for %s' % (len(car_entries), imagefile))

        if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
        else: index_car = 0
        while button != 27 and index_car >= 0 and index_car < len(car_entries):
            car_entry = car_entries[index_car]
            carid = carField(car_entry, 'id')
            roi = bbox2roi (carField(car_entry, 'bbox'))
            imagefile = carField(car_entry, 'imagefile')

            # assign label for display
            if carid in car_statuses.keys():
                label = car_statuses[carid]
            else:
                label = carField(car_entry, 'name')
                if label == 'object': label = ''
            logging.debug ('label: "' + (label or '') + '"')

            display = image.copy()
            drawRoi (display, roi, label)

            disp_scale = params['disp_scale']
            display = cv2.resize(display, (0,0), fx=disp_scale, fy=disp_scale)
            cv2.imshow('show', display)
            button = params['key_reader'].readKey()

            if button == keys['left']:
                logging.debug ('prev car')
                index_car -= 1
            elif button == keys['right']:
                logging.debug ('next car')
                index_car += 1
            elif button == keys['del']:
                logging.info ('delete')
                car_statuses[carid] = 'badroi'
                index_car += 1
            elif button in keys.keys():  # any of the names added to keys in this function
                logging.info (keys[button])
                car_statuses[carid] = keys[button]
                index_car += 1

        if button == keys['left']:
            logging.debug ('prev image')
            if index_im == 0:
                logging.warning ('already the first image')
            else:
                index_im -= 1
                index_car = -1
        else: 
            logging.debug ('next image')
            index_im += 1

    # actually delete or update
    for (carid, status) in car_statuses.iteritems():
        if status == 'badroi':
            deleteCar (c, carid)
        elif status == '':
            c  # nothing
        else:
            c.execute('UPDATE cars SET name=? WHERE id=?', (status, carid))



def classifyColor (c, params = {}):
    logging.info ('==== classifyColor ====')
    setParamUnlessThere (params, 'disp_scale', 1.5)
    setParamUnlessThere (params, 'car_constraint',   '1')
    setParamUnlessThere (params, 'image_processor',     ReaderVideo())
    setParamUnlessThere (params, 'key_reader',       KeyReaderUser())
    keys = getCalibration()

    keys[ord(' ')] = ''
    keys[ord('k')] = 'black'
    keys[ord('w')] = 'white'
    keys[ord('b')] = 'blue'
    keys[ord('y')] = 'yellow'
    keys[ord('r')] = 'red'
    keys[ord('g')] = 'green'
    keys[ord('s')] = 'gray'

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

    c.execute('SELECT imagefile FROM images')
    image_entries = c.fetchall()

    if 'imagefile_start' in params.keys(): 
        imagefile_start = params['imagefile_start']
        try:
            index_im = image_entries.index((imagefile_start,))
            logging.info ('starting from image %d' % index_im)
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

        img = params['image_processor'].imread(imagefile)

        c.execute('SELECT * FROM cars WHERE imagefile=? AND (%s)' % params['car_constraint'], (imagefile,))
        car_entries = c.fetchall()
        logging.info (str(len(car_entries)) + ' cars found for ' + imagefile)

        if index_car == -1: index_car = len(car_entries) - 1  # did 'prev image'
        else: index_car = 0
        while button != 27 and index_car >= 0 and index_car < len(car_entries):
            car_entry = car_entries[index_car]
            carid     = carField(car_entry, 'id')
            roi       = bbox2roi (carField(car_entry, 'bbox'))
            imagefile = carField(car_entry, 'imagefile')

            # assign label for display
            if carid in car_statuses.keys():
                label = car_statuses[carid]
            else:
                label = carField(car_entry, 'color')
            logging.debug ('label: "' + (label or '') + '"')

            img_show = img.copy()
            drawRoi (img_show, roi, label, color_config[label or ''])

            # draw image
            disp_scale = params['disp_scale']
            display = cv2.resize(img_show, (0,0), fx=disp_scale, fy=disp_scale)
            cv2.imshow('show', display)
            button = params['key_reader'].readKey()

            # checking button inside iterating cars
            if button == keys['left']:
                logging.debug ('prev')
                index_car -= 1
            elif button == keys['right']:
                logging.debug ('next')
                index_car += 1
            elif button == keys['del']:
                logging.info ('delete')
                car_statuses[carid] = 'badroi'
                index_car += 1
            elif button in keys.keys():
                logging.info (keys[button])
                car_statuses[carid] = keys[button]
                index_car += 1

        # checking button inside iterating images (after exit from inner loop)
        if button == keys['left']:
            logging.debug ('prev image')
            if index_im == 0:
                logging.warning  ('already the first image')
            else:
                index_im -= 1
                index_car = -1
        else: 
            logging.debug ('next image')
            index_im += 1

    # actually delete or update
    for (carid, status) in car_statuses.iteritems():
        if status == 'badroi':
            deleteCar (c, carid)
        elif status == '':
            c.execute('UPDATE cars SET color=? WHERE id=?', (None, carid))
        else:
            c.execute('UPDATE cars SET color=? WHERE id=?', (status, carid))





# helper global vars for mouse callback
xpress, ypress = None, None
mousePressed = False
mouseReleased = False

# mouse callback for labelling matches
def __monitorPressRelease__ (event,x,y,flags,param):
    global xpress, ypress, mousePressed, mouseReleased

    if event == cv2.EVENT_LBUTTONDOWN:
        xpress, ypress = x, y
        assert not mouseReleased
        mousePressed = True

    elif event == cv2.EVENT_LBUTTONUP:
        xpress, ypress = x, y
        assert not mousePressed
        mouseReleased = True


def __drawMatch__ (img, roi1, roi2):
    offsetY = img.shape[0] / 2;
    color = (0, 255, 0)
    roi2[0] += offsetY
    roi2[2] += offsetY
    drawRoi (img, roi1, None, color)
    drawRoi (img, roi2, None, color)
    center1 = getCenter(roi1)
    center2 = getCenter(roi2)
    cv2.line(img, center1, center2, color)


def __findPressedCar__ (x, y, cars):
    for i in range(len(cars)):
        roi = carField(cars[i], 'roi')
        if x >= roi[1] and x < roi[3] and y >= roi[0] and y < roi[2]:
            return i
    return None 


def labelMatches (c, params = {}):
    '''
    Manually label matching cars in the provided dataset.

    At the start you should see a window with two images one under another.
    - Press and hold the mouse at a Bbox in the top, and release at a Bbox in the bottom.
        That will add a match between this pair of Bboxes.
        If one of the two Bboxes were matched to something already, match won't be added.
    - Click at a Bbox in the top, and press DEL. 
        That will remove a match if the top Bbox was matched
    - Press 'Right' (according to your calibration) or "Left'.
        That will change the image pair.
    - Press 'Esc' to save changes and exit.
    - Pass 'imagefile_start' number in parameters to start with a certain image pair.
    '''
    logging.info ('==== labelMatches ====')
    setParamUnlessThere (params, 'debug', False)
    setParamUnlessThere (params, 'disp_scale', 1.5)
    setParamUnlessThere (params, 'image_processor',     ReaderVideo())
    setParamUnlessThere (params, 'key_reader',       KeyReaderUser())
    keys = getCalibration()

    createTableMatches(c)

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
    cv2.setMouseCallback('show', __monitorPressRelease__)
    global mousePressed, mouseReleased, xpress, ypress

    button = -1
    while button != 27 and index_im < len(image_entries):
        (imagefile1,) = image_entries[index_im - 1]
        (imagefile2,) = image_entries[index_im]
    
        img1 = params['image_processor'].imread(imagefile1)
        img2 = params['image_processor'].imread(imagefile2)
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
        for car in cars1: drawRoi (img1, carField(car, 'roi'))
        for car in cars2: drawRoi (img2, carField(car, 'roi'))

        i1 = i2 = None

        # each cycle is some some key is pressed
        #   fortunately all the keys mean some serious update
        selectedMatch = None
        needRedraw = True
        button = -1
        while button == -1:

            img_stack = np.vstack((img1, img2))

            if needRedraw:

                # find existing matches, and make a map
                matchesOf1 = {}
                matchesOf2 = {}
                for j1 in range(len(cars1)):
                    car1 = cars1[j1]
                    for j2 in range(len(cars2)):
                        car2 = cars2[j2]
                        s = '''SELECT match FROM matches WHERE carid = ?
                               INTERSECT
                               SELECT match FROM matches WHERE carid = ?'''
                        c.execute(s, (carField(car1, 'id'), carField(car2, 'id')))
                        matches = c.fetchall()
                        if len(matches) > 0:
                            assert len(matches) == 1  # no duplicate matches
                            roi1 = carField(car1, 'roi')
                            roi2 = carField(car2, 'roi')
                            __drawMatch__ (img_stack, roi1, roi2)
                            matchesOf1[j1] = matches[0][0]
                            matchesOf2[j2] = matches[0][0]

                # draw image
                disp_scale = params['disp_scale'] / 2
                img_show = cv2.resize(img_stack, (0,0), fx=disp_scale, fy=disp_scale)
                cv2.imshow('show', img_show)
                logging.info ('%d matches found between the pair' % len(matchesOf1))
                needRedraw = False

            # process mouse callback effect (button has been pressed)
            if mousePressed:
                i2 = None  # reset after the last unsuccessful match
                logging.debug ('pressed  x=%d, y=%d' % (xpress, ypress))
                xpress /= disp_scale
                ypress /= disp_scale
                i1 = __findPressedCar__ (xpress, ypress, cars1)
                if i1 is not None: logging.debug ('found pressed car number: %d' % i1)
                mousePressed = False

            # process mouse callback effect (button has been released)
            if mouseReleased:
                logging.debug ('released x=%d, y=%d' % (xpress, ypress))
                xpress /= disp_scale
                ypress /= disp_scale
                i2 = __findPressedCar__ (xpress, ypress - yoffset, cars2)
                if i2 is not None: logging.debug ('found released car number: %d' % i2)
                mouseReleased = False

            # if we could find pressed and released cars, add match
            if i1 is not None and i2 is not None:

                # if one of the cars in the new match is already matched, discard
                if i1 in matchesOf1 or i2 in matchesOf2:
                    logging.warning ('one or two connected cars is already matched')
                    i1 = i2 = None

                else:
                    # add the match to the list
                    carid1 = carField(cars1[i1], 'id')
                    carid2 = carField(cars2[i2], 'id')
                    logging.debug ('i1 = %d, i2 = %d' % (i1, i2))
                    logging.info ('detected a match')

                    # find a free match index
                    c.execute('SELECT MAX(match) FROM matches')
                    matchid = int(c.fetchone()[0]) + 1

                    c.execute('INSERT INTO matches(match, carid) VALUES (?,?)', (matchid, carid1))
                    c.execute('INSERT INTO matches(match, carid) VALUES (?,?)', (matchid, carid2))

                    # display the match
                    roi1 = carField(cars1[i1], 'roi')
                    roi2 = carField(cars2[i2], 'roi')
                    roi2[0] += yoffset
                    roi2[1] += yoffset
                    __drawMatch__ (img_stack, roi1, roi2)

                    # reset when a new match is made
                    needRedraw = True
                    i1 = i2 = None

            # stay inside the loop inside one image pair until some button is pressed
            button = params['key_reader'].readKey()

        # process pressed key (all except exit)
        if button == keys['left']:
            logging.debug ('prev image pair')
            if index_im == 1:
                logging.warning ('already the first image pair')
            else:
                index_im -= 1
        elif button == keys['right']:
            logging.debug ('next image pair')
            index_im += 1  # exit at last image pair from outer loop
        elif button == keys['del']:
            # if any car was selected, and it is matched
            if i1 is not None and i1 in matchesOf1:
                match = matchesOf1[i1]
                carid1 = carField(cars1[i1], 'id')
                logging.info ('deleting match %d' % match)
                c.execute('DELETE FROM matches WHERE match = ? AND carid = ?', (match, carid1))
            else:
                logging.debug ('delete is pressed, but no match is selected')

