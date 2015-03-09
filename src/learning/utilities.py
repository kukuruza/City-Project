import numpy as np



#
# roi - all inclusive, like in Matlab
# crop = im[roi[0]:roi[2]+1, roi[1]:roi[3]+1] (differs from Matlab)
#
def bbox2roi (bbox):
    assert (isinstance(bbox, list) and len(bbox) == 4)
    return [bbox[1], bbox[0], bbox[3]+bbox[1]-1, bbox[2]+bbox[0]-1]

def roi2bbox (roi):
    assert (isinstance(roi, list) and len(roi) == 4)
    return [roi[1], roi[0], roi[3]-roi[1]+1, roi[2]-roi[0]+1]

def image2ghost (image, backimage):
    assert (image is not None)
    assert (backimage is not None)
    return np.uint8((np.int32(image) - np.int32(backimage)) / 2 + 128)

def getCenter (roi):
    return (int((roi[0] + roi[2]) * 0.5), int((roi[1] + roi[3]) * 0.5))

def bottomCenter (roi):
    return (roi[0] * 0.25 + roi[2] * 0.75, roi[1] * 0.5 + roi[3] * 0.5)

