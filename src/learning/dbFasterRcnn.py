import os, sys, os.path as op
import logging
import glob
import shutil
import sqlite3
import xml.etree.ElementTree as ET
from xml.dom import minidom
from helperDb    import carField, imageField
from helperSetup import setParamUnlessThere, assertParamIsThere
from helperImg   import ReaderVideo, ProcessorImagefile
from dbUtilities import bbox2roi, roi2bbox, bottomCenter, drawRoi
from dbModify    import isRoiAtBorder



def _prettify_ (elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def _writeXmlString_ (c, imagefile, car_entries, params = {}):
    assertParamIsThere (params, 'out_dataset')
    setParamUnlessThere (params, 'annotation', 'automatic')

    # will need that later
    c.execute('SELECT src, width, height FROM images WHERE imagefile=?', (imagefile,))
    src, imwidth, imheight = c.fetchone()

    top = ET.Element('annotation')

    # folder, filename
    _, filename = op.split(imagefile)
    child = ET.SubElement(top, 'folder')
    child.text = params['out_dataset']
    child = ET.SubElement(top, 'filename')
    child.text = filename

    # source
    child = ET.SubElement(top, 'source')
    grandchild = ET.SubElement(child, 'database')
    grandchild.text = 'CityCam database'
    grandchild = ET.SubElement(child, 'annotation')
    grandchild.text = params['annotation']
    grandchild = ET.SubElement(child, 'image')
    grandchild.text = src

    # size
    child = ET.SubElement(top, 'size')
    grandchild = ET.SubElement(child, 'width')
    grandchild.text = str(imwidth)
    grandchild = ET.SubElement(child, 'height')
    grandchild.text = str(imheight)
    grandchild = ET.SubElement(child, 'depth')
    grandchild.text = str(3)

    # bboxes
    for car_entry in car_entries:
        child = ET.SubElement(top, 'object')
        grandchild = ET.SubElement(child, 'name')
        grandchild.text = carField(car_entry, 'name')
        grandchild = ET.SubElement(child, 'pose')
        grandchild.text = 'Unspecified'
        grandchild = ET.SubElement(child, 'truncated')

        roi = bbox2roi(carField(car_entry, 'bbox'))
        params['border_thresh_perc'] = 0.02
        grandchild.text = str(int(isRoiAtBorder(roi, imwidth, imheight, params)))
        grandchild = ET.SubElement(child, 'bndbox')
        greatgrandchild = ET.SubElement(grandchild, 'xmin')
        greatgrandchild.text = str(roi[1])
        greatgrandchild = ET.SubElement(grandchild, 'ymin')
        greatgrandchild.text = str(roi[0])
        greatgrandchild = ET.SubElement(grandchild, 'xmax')
        greatgrandchild.text = str(roi[3])
        greatgrandchild = ET.SubElement(grandchild, 'ymax')
        greatgrandchild.text = str(roi[2])

    return _prettify_(top)




def exportSparseCars (c, out_dataset, params = {}):
    '''
    Export non-empty video frames and corresponding bboxes to PASCAL format.
    Not all the cars are assumed to be detected, so will also export the foreground mask

    We keep data as videos and sql database with boxes.
    faster-rcnn/py-faster-rcnn keeps data as images and xml files with boxes.

    out_dataset is the root folder of dataset. It contains:
      Annotations
      JPEGImages
      Masks  (only this one is specific to us)
    '''

    logging.info ('==== exportSparseCars ====')
    setParamUnlessThere (params, 'constraint', '1')
    setParamUnlessThere (params, 'relpath',      os.getenv('CITY_DATA_PATH'))
    setParamUnlessThere (params, 'image_reader', ReaderVideo())
    setParamUnlessThere (params, 'image_writer', ProcessorImagefile())
    params['out_dataset'] = out_dataset

    if op.exists (op.join(params['relpath'], out_dataset)):
        shutil.rmtree (op.join(params['relpath'], out_dataset))
    os.makedirs (op.join(params['relpath'], out_dataset, 'JPEGImages'))
    os.makedirs (op.join(params['relpath'], out_dataset, 'Masks'))
    os.makedirs (op.join(params['relpath'], out_dataset, 'Annotations'))

    # for every image
    counter = 0
    c.execute('SELECT imagefile, maskfile FROM images')
    for imagefile, maskfile in c.fetchall():
        logging.debug ('working with image %s' % (imagefile,))

        # find cars in that image
        c.execute('SELECT * FROM cars WHERE imagefile=? AND (%s)' % params['constraint'], 
                  (imagefile,))
        car_entries = c.fetchall()

        if not car_entries:
            logging.debug ('no bboxes found for image %s' % (imagefile,))
            continue

        # read and write image and mask
        image = params['image_reader'].imread(imagefile)
        mask  = params['image_reader'].maskread(maskfile)
        imagepath = op.join(out_dataset, 'JPEGImages', '%06d.jpg' % counter)
        maskpath  = op.join(out_dataset, 'Masks', '%06d.png' % counter)
        params['image_writer'].imwrite  (image, imagepath)
        params['image_writer'].maskwrite(mask,  maskpath)
        counter += 1

        # write annotations
        name = op.splitext(op.basename(imagefile))[0]
        xmlpath = op.join(params['relpath'], out_dataset, 'Annotations', name + '.xml')
        with open(xmlpath, 'w') as f:
            xmlstr = _writeXmlString_ (c, imagefile, car_entries, params)
            f.write(xmlstr)






