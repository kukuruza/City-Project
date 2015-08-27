import sys, os, os.path as op
import numpy as np
import cv2
import logging
import h5py
import random  # for random browsing
import helperKeys
import helperSetup

'''
Images are written to be compatible with caffe. 
Need some verification and processing to read/write images, get dimensions, etc
'''



def getImage (f, index):
    image = f['data'][index,:,:,:]
    assert len(image.shape) == 3 and image.shape[0] == 3
    image = np.transpose(np.multiply(image, 255).astype(np.uint8), (1,2,0))
    return image

def getId (f, index):
    # no check if label is in the dataset. Let it raise an exception
    imageid = f['ids'][index,0,0,0]
    return int(imageid)

def getLabel (f, index):
    # no check if label is in the dataset. Let it raise an exception
    label = f['label'][index,0,0,0]
    return int(label)

def getImageDims (f):
    dims = tuple( list(f['data'].shape)[1:] )
    return (dims[1], dims[2], dims[0])

def getNum (f):
    if 'data' not in f: return 0
    return f['data'].len()


def writeNextPatch (f, image, image_id, label = None):
    ''' Write a patch to open hdf5 file 'f', with its id and label. '''

    image = np.transpose(image.astype('float32'), (2,0,1)) # will be CHxHxW
    image /= 255.0
    (d1,d2,d3) = image.shape

    # if the file is new and empty, create datasets
    if 'data' not in f:
        dset_data = f.create_dataset('data', (0,d1,d2,d3), maxshape=(None,d1,d2,d3), chunks=(500,d1,d2,d3))
        dset_ids  = f.create_dataset('ids',  (0,1,1,1),    maxshape=(None,1,1,1), chunks=(500,1,1,1))
        if label is not None:
            dset_label = f.create_dataset('label', (0,1,1,1), maxshape=(None,1,1,1), chunks=(500,1,1,1))

    # resize to one more
    numImages = getNum (f)
    f['data'].resize  (numImages+1, axis=0)
    f['ids'].resize   (numImages+1, axis=0)
    if label is not None:
        f['label'].resize (numImages+1, axis=0)

    f['data'][numImages,:,:,:] = image
    f['ids'] [numImages,0,0,0] = image_id
    if label is not None:
        f['label'][numImages,0,0,0] = label



def mergeH5 (in_f1, in_f2, out_f):
    ''' Concatenate 'in_f2' to the end of 'in_f1'. Save the output as 'out_f'. '''
    logging.info ('=== exporting.mergeHDF5 ===')

    data1  = in_f1['data'][:]
    ids1   = in_f1['ids'][:]
    label1 = in_f1['label'][:] if 'label' in in_f1 else None
    assert data1.size != 0
    assert ids1.size != 0
    assert len(ids1.shape) == 4
    assert label1 is None or len(label1.shape) == 4

    data2  = in_f2['data'][:]
    ids2   = in_f2['ids'][:]
    label2 = in_f2['label'][:] if 'label' in in_f2 else None
    assert data2.size != 0
    assert ids2.size != 0
    assert len(ids2.shape) == 4
    assert label2 is None or len(label2.shape) == 4

    # make sure the patches have the same dimensions
    assert (list(data1.shape)[1:] == list(data2.shape)[1:])
    # make sure labels are present or not present in both files
    assert (label1 is not None and label2 is not None) or (label1 is None and label2 is None)
    # make sure ids are present in both files
    assert ids1 is not None and ids2 is not None

    # TODO: if dataset are too big, need to avoid adding them in memory

    out_f['data'] = np.vstack((data1, data2))
    out_f['ids']  = np.vstack((ids1, ids2))
    if label1 is not None: 
        out_f['label']  = np.vstack((label1, label2))



def viewPatches (f, params = {}):
    '''
    Browse through images/labels from an opened hdf5 file
    '''
    helperSetup.setParamUnlessThere (params, 'random', False)
    helperSetup.setParamUnlessThere (params, 'scale', 1)
    helperSetup.setParamUnlessThere (params, 'key_reader', helperKeys.KeyReaderUser())
    keys = helperKeys.getCalibration()

    numImages = getNum(f)
    logging.info ('dataset has %d images' % numImages)
    logging.info ('dataset image dims: %d x %d x %d' % getImageDims(f))

    key = -1
    index = 0
    while key != keys['esc']:
        image = getImage(f, index)
        logging.debug ('image dims: %d x %d x %d' % image.shape)

        logging.info ('index: %d' % index)
        if 'label' in f: logging.info ('image label: %d' % getLabel(f, index))

        display = cv2.resize(image, (0,0), fx=params['scale'], fy=params['scale'])
        cv2.imshow ('show', display)
        key = params['key_reader'].readKey()

        if   key == keys['left']:
            logging.debug ('prev image')
            if params['random']: index = np.random.randint(0, numImages)
            else: index = (index - 1) % numImages
        elif key == keys['right']:
            logging.debug ('next image')
            if params['random']: index = np.random.randint(0, numImages)
            else: index = (index + 1) % numImages
