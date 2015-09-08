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


def writeNextPatch (f, image, image_id, label):
    ''' Write a patch to open hdf5 file 'f', with its id and label. '''

    image = np.transpose(image.astype('float32'), (2,0,1)) # will be CHxHxW
    image /= 255.0
    (d1,d2,d3) = image.shape

    # if the file is new and empty, create datasets
    if 'data' not in f:
        f.create_dataset('data', (0,d1,d2,d3), maxshape=(None,d1,d2,d3), chunks=(100,d1,d2,d3))
        f.create_dataset('ids',  (0,1,1,1),    maxshape=(None,1,1,1), chunks=(100,1,1,1))
        f.create_dataset('label', (0,1,1,1), maxshape=(None,1,1,1), chunks=(100,1,1,1))

    # resize to one more
    numImages = getNum (f)
    f['data'].resize  (numImages+1, axis=0)
    f['ids'].resize   (numImages+1, axis=0)
    f['label'].resize (numImages+1, axis=0)

    f['data'][numImages,:,:,:] = image
    f['ids'] [numImages,0,0,0] = image_id
    f['label'][numImages,0,0,0] = label



def shuffle (f):
    ''' Shuffle data, labels, and ids in input 'f' '''
    logging.info ('=== helperH5.shuffle ===')

    data   = f['data'][:]
    ids    = f['ids'][:]
    labels = f['label'][:]

    order = np.random.permutation(data.shape[0])
    f['data'][:]  = data[order,:,:,:]
    f['ids'][:]   = ids[order,:,:,:]
    f['label'][:] = labels[order,:,:,:]



def multipleOf (f, multiple):
    ''' Make the number of patches to be a multiple of 'multiple'. Discard the rest. '''
    logging.info ('=== helperH5.multipleOf ===')
    assert isinstance(multiple, int) and multiple > 0

    nowN = f['data'].shape[0]
    wantN = nowN / multiple * multiple
    logging.info ('out of %d patches will leave %d' % (nowN, wantN))

    f['data'].resize (wantN, 0)
    f['ids'].resize (wantN, 0)
    f['label'].resize (wantN, 0)


def crop (f_in, f_out, number, params = {}):
    ''' Keep first 'number' elements. Crop the rest. '''
    logging.info ('=== helperH5.crop ===')
    helperSetup.setParamUnlessThere (params, 'chunk', 100)
    assert isinstance(number, int) and number > 0

    if number > getNum(f_in):
        raise Exception ('provided number = %d > N elements = %d' % (number, getNum(f)))

    # if the file is new and empty, create datasets
    if 'data' not in f_out:
        (d0,d1,d2,d3) = f_in['data'].shape
        ch = params['chunk']
        f_out.create_dataset('data', (0,d1,d2,d3), maxshape=(None,d1,d2,d3), chunks=(ch,d1,d2,d3))
        f_out.create_dataset('ids',  (0,1,1,1),    maxshape=(None,1,1,1), chunks=(ch,1,1,1))
        f_out.create_dataset('label', (0,1,1,1), maxshape=(None,1,1,1), chunks=(ch,1,1,1))

    f_out['data'].resize (number, 0)
    f_out['ids'].resize (number, 0)
    f_out['label'].resize (number, 0)
    f_out['data'][:]  = f_in['data'][:number]
    f_out['ids'][:]   = f_in['ids'][:number]
    f_out['label'][:] = f_in['label'][:number]



def merge (in_f1, in_f2, out_f, params = {}):
    ''' Concatenate 'in_f2' to the end of 'in_f1'. Save the output as 'out_f'. '''
    logging.info ('=== helperH5.merge ===')

    # one of in_f1 or in_f2 should be non empty
    if   'data' in in_f1:
        dims = tuple( list(in_f1['data'].shape)[1:] )
    elif 'data' in in_f2:
        dims = tuple( list(in_f2['data'].shape)[1:] )
    else:
        raise Exception('both in_f1 and in_f2 can\'t be empty')

    if 'data' in in_f1 and 'ids' in in_f1 and 'label' in in_f1:
        data1  = in_f1['data'][:]
        ids1   = in_f1['ids'][:]
        label1 = in_f1['label'][:]
    else:
        data1  = np.empty((0,dims[0],dims[1],dims[2]), dtype=float)
        ids1   = np.empty((0,1,1,1), dtype=float)
        label1 = np.empty((0,1,1,1), dtype=float)
    assert len(ids1.shape) == 4
    assert len(label1.shape) == 4

    if 'data' in in_f2 and 'ids' in in_f2 and 'label' in in_f2:
        data2  = in_f2['data'][:]
        ids2   = in_f2['ids'][:]
        label2 = in_f2['label'][:]
    else:
        data2  = np.empty((0,dims[0],dims[1],dims[2]), dtype=float)
        ids2   = np.empty((0,1,1,1), dtype=float)
        label2 = np.empty((0,1,1,1), dtype=float)
    assert len(ids2.shape) == 4
    assert len(label2.shape) == 4

    # make sure the patches have the same dimensions
    assert (list(data1.shape)[1:] == list(data2.shape)[1:])
    # make sure labels are present or not present in both files
    assert label1 is not None and label2 is not None
    # make sure ids are present in both files
    assert ids1 is not None and ids2 is not None

    # TODO: if dataset are too big, need to avoid adding them in memory

    data = np.vstack((data1, data2))
    ids = np.vstack((ids1, ids2))
    labels = np.vstack((label1, label2))

    if 'data' in out_f and 'ids' in out_f and 'label' in out_f:
        wantNum = data.shape[0]
        out_f['data'].resize  (wantNum, axis=0)
        out_f['ids'].resize   (wantNum, axis=0)
        out_f['label'].resize (wantNum, axis=0)
    else:
        (d0,d1,d2,d3) = data.shape
        out_f.create_dataset('data', (d0,d1,d2,d3), maxshape=(None,d1,d2,d3), chunks=(100,d1,d2,d3))
        out_f.create_dataset('ids',  (d0,1,1,1),    maxshape=(None,1,1,1), chunks=(100,1,1,1))
        out_f.create_dataset('label',(d0,1,1,1),    maxshape=(None,1,1,1), chunks=(100,1,1,1))

    out_f['data'][:] = data
    out_f['ids'][:]  = ids
    out_f['label'][:] = labels



def viewPatches (f, params = {}):
    '''
    Browse through images/labels from an opened hdf5 file
    '''
    logging.info ('=== helperH5.viewPatches ===')
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
