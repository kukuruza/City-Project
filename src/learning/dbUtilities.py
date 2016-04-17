import numpy as np
import cv2
import scipy.cluster.hierarchy
import matplotlib.pyplot
import matplotlib.pyplot as plt  # for colormaps
import sys, os, os.path as op
import logging
from scipy.stats import gamma
from math import atan
from helperSetup import setParamUnlessThere



#
# roi - all inclusive, like in Matlab
# crop = im[roi[0]:roi[2]+1, roi[1]:roi[3]+1] (differs from Matlab)
#
def bbox2roi (bbox):
    assert ((isinstance(bbox, list) or isinstance(bbox, tuple)) and len(bbox) == 4)
    return [bbox[1], bbox[0], bbox[3]+bbox[1]-1, bbox[2]+bbox[0]-1]

def roi2bbox (roi):
    assert ((isinstance(roi, list) or isinstance(roi, tuple)) and len(roi) == 4)
    return [roi[1], roi[0], roi[3]-roi[1]+1, roi[2]-roi[0]+1]

def image2ghost (image, backimage):
    assert (image is not None)
    assert (backimage is not None)
    return np.uint8((np.int32(image) - np.int32(backimage)) / 2 + 128)

def getCenter (roi):
    ''' returns (x,y) '''
    return (int((roi[1] + roi[3]) * 0.5), int((roi[0] + roi[2]) * 0.5))

def bottomCenter (roi):
    return (roi[0] * 0.25 + roi[2] * 0.75, roi[1] * 0.5 + roi[3] * 0.5)


def drawRoi (img, roi, label = None, color = None):
    font = cv2.FONT_HERSHEY_SIMPLEX
    if label is None: label = ''
    if color is None:
        if label == 'border':
            color = (0,255,255)
        elif label == 'badroi':
            color = (0,0,255)
        else:
            color = (255,0,0)
        thickness = 1
    else:
        thickness = 2
    cv2.rectangle (img, (roi[1], roi[0]), (roi[3], roi[2]), color, thickness)
    cv2.putText (img, label, (roi[1], roi[0] - 5), font, 0.6, color, thickness)


def drawScoredRoi (img, roi, label = None, score = 1.0):
    assert (score >= 0 and score <= 1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    if label is None: label = ''
    if score is None:
        score = 1
        thickness = 1
    else:
        thickness = 2
    color = tuple([int(x * 255) for x in plt.cm.jet(float(score))][0:3])
    cv2.rectangle (img, (roi[1], roi[0]), (roi[3], roi[2]), color, thickness)
    cv2.putText (img, label, (roi[1], roi[0] - 5), font, 0.6, score, thickness)



#
# expandRoiFloat expands a ROI, and clips it within borders
#
def expandRoiFloat (roi, (imheight, imwidth), (perc_y, perc_x), integer_result = True):
    '''
    floats are rounded to the nearest integer
    '''
    if (perc_y, perc_x) == (0, 0): return roi

    half_delta_y = float(roi[2] + 1 - roi[0]) * perc_y / 2
    half_delta_x = float(roi[3] + 1 - roi[1]) * perc_x / 2
    # the result must be within (imheight, imwidth)
    bbox_height = roi[2] + 1 - roi[0] + half_delta_y * 2
    bbox_width  = roi[3] + 1 - roi[1] + half_delta_x * 2
    if bbox_height > imheight or bbox_width > imwidth:
        logging.warning ('expanded bbox of size (%d,%d) does not fit into image (%d,%d)' %
            (bbox_height, bbox_width, imheight, imwidth))
        # if so, decrease half_delta_y, half_delta_x
        coef = min(imheight / bbox_height, imwidth / bbox_width)
        logging.warning ('decreased bbox to (%d,%d)' % (bbox_height, bbox_width))
        bbox_height *= coef
        bbox_width  *= coef
        #logging.warning ('imheight, imwidth (%d,%d)' % (imheight, imwidth))
        logging.warning ('decreased bbox to (%d,%d)' % (bbox_height, bbox_width))
        half_delta_y = (bbox_height - (roi[2] + 1 - roi[0])) * 0.5
        half_delta_x = (bbox_width  - (roi[3] + 1 - roi[1])) * 0.5
        #logging.warning ('perc_y, perc_x: %.1f, %1.f: ' % (perc_y, perc_x))
        #logging.warning ('original roi: %s' % str(roi))
        #logging.warning ('half_delta-s y: %.1f, x: %.1f' % (half_delta_y, half_delta_x))
    # and a small epsilon to account for floating-point imprecisions
    EPS = 0.001
    # expand each side
    roi[0] -= (half_delta_y - EPS)
    roi[1] -= (half_delta_x - EPS)
    roi[2] += (half_delta_y - EPS)
    roi[3] += (half_delta_x - EPS)
    # move to clip into borders
    if roi[0] < 0:
        roi[2] += abs(roi[0])
        roi[0] = 0
    if roi[1] < 0:
        roi[3] += abs(roi[1])
        roi[1] = 0
    if roi[2] > imheight-1:
        roi[0] -= abs((imheight-1) - roi[2])
        roi[2] = imheight-1
    if roi[3] > imwidth-1:
        roi[1] -= abs((imwidth-1) - roi[3])
        roi[3] = imwidth-1
    # check that now averything is within borders (bbox is not too big)
    assert roi[0] >= 0 and roi[1] >= 0, str(roi)
    assert roi[2] <= imheight-1 and roi[3] <= imwidth-1, str(roi)
    # make integer
    if integer_result:
        roi = [int(round(x)) for x in roi]
    return roi


#
# expands a ROI to keep 'ratio', and maybe more, up to 'expand_perc'
#
def expandRoiToRatio (roi, (imheight, imwidth), expand_perc, ratio):
    bbox = roi2bbox(roi)
    # adjust width and height to ratio
    height = float(roi[2] + 1 - roi[0])
    width  = float(roi[3] + 1 - roi[1])
    if height / width < ratio:
       perc = ratio * width / height - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (perc, 0), integer_result = False)
    else:
       perc = height / width / ratio - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (0, perc), integer_result = False)
    # additional expansion
    perc = (1 + expand_perc) / (1 + perc) - 1
    if perc > 0:
        roi = expandRoiFloat (roi, (imheight, imwidth), (perc, perc), integer_result = False)
    roi = [int(round(x)) for x in roi]
    return roi



def gammaProb (x, max_value, shape):
    '''
    x is distributed with Gamma(shape, scale).  
    (loose) 1 < Gamma.shape < +inf (tight)
    
    Gamma.scale is set so that the maximim of pdf equals max_value, 
    Gamma.shape is input
    '''
    #if max_value == 0: return 0  ### WTF is this for???
    if shape <= 1: raise Exception ('gammaProb: shape should be > 1')
    scale = float(max_value) / (shape - 1)
    return gamma.pdf(x, shape, 0, scale) / gamma.pdf(max_value, shape, 0, scale)



def overlapRatio (roi1, roi2):
    assert (len(roi1) == 4 and len(roi2) == 4)
    if roi1 == roi2: return 1  # same object
    dy = min(roi1[2], roi2[2]) - max(roi1[0], roi2[0])
    dx = min(roi1[3], roi2[3]) - max(roi1[1], roi2[1])
    if dy <= 0 or dx <= 0: return 0
    area1 = (roi1[2] - roi1[0]) * (roi1[3] - roi1[1])
    area2 = (roi2[2] - roi2[0]) * (roi2[3] - roi2[1])
    inters = dx * dy
    union  = area1 + area2 - inters
    logging.debug('inters: ' + str(inters) + ', union: ' +  str(union))
    assert (union >= inters and inters > 0)
    return float(inters) / union


def hierarchicalClusterRoi (rois, params = {}):
    if not rois:         return [], [], []
    elif len(rois) == 1: return rois, [0], [1]

    setParamUnlessThere (params, 'debug_clustering', False)

    N = len(rois)
    pairwise_distances = np.zeros((N,N), dtype = float)

    for j in range(N):
        for i in range(N):
            pairwise_distances[i][j] = 1 - overlapRatio(rois[i], rois[j])
    condensed_distances = scipy.spatial.distance.squareform (pairwise_distances)

    # perform clustering
    Z = scipy.cluster.hierarchy.linkage (condensed_distances)
    clusters = scipy.cluster.hierarchy.fcluster (Z, params['cluster_threshold'], 'distance')
    logging.debug('clusters: ' + str(clusters))

    # get centers as simple mean
    centers = []
    scores = []
    for cluster in list(set(clusters)):
        rois_cluster = [x for i, x in enumerate(rois) if clusters[i] == cluster]
        centers.append (list( np.mean(np.array(rois_cluster), 0).astype(int) ))
        scores.append (atan(len(rois_cluster)) / (np.pi / 2))
    logging.debug ('centers: ' + str(centers))
    logging.info ('out of ' + str(len(clusters)) + ' ROIs left ' + str(len(centers)))

    # show clusters
    if params['debug_clustering']:
        scipy.cluster.hierarchy.dendrogram(Z)
        matplotlib.pyplot.waitforbuttonpress()
        matplotlib.pyplot.close()
    logging.debug(Z)

    return centers, clusters, scores



# polygon == [pts], pt = (x, y)
# current naive implementation
def polygon2roi (polygon):
    xs = []
    ys = []
    for pt in polygon:
        xs.append(pt[0])
        ys.append(pt[1])
    return [min(ys), min(xs), max(ys), max(xs)]


# polygon == [pts], pt = (x, y)
def overlapRatioPoly (polygon1, polygon2, params):
    mask1 = np.zeros(params['imgshape'], dtype = np.uint8)
    cv2.fillPoly (mask1, [np.array(polygon1, dtype = np.int32)], (127))
    mask2 = np.zeros(params['imgshape'], dtype = np.uint8)
    cv2.fillPoly (mask2, [np.array(polygon2, dtype = np.int32)], (127))
    # show clusters
    if params['debug_clustering']:
        cv2.imshow('mask', mask1 + mask2)
        cv2.waitKey(-1)
    inters = np.logical_and(mask1, mask2)
    union  = np.logical_or (mask1, mask2)
    nInters = float(np.count_nonzero(inters))
    nUnion  = float(np.count_nonzero(union))
    return nInters / nUnion if nUnion > 0 else 0


def hierarchicalClusterPolygons (polygons, params):
    if not polygons:         return [], []
    elif len(polygons) == 1: return [polygon2roi(polygons[0])], [0]

    params = setParamUnlessThere (params, 'debug_clustering', False)

    N = len(polygons)
    pairwise_distances = np.zeros((N,N), dtype = float)
    for j in range(N):
        for i in range(N):
            pairwise_distances[i][j] = 1 - overlapRatioPoly(polygons[i], polygons[j], params)
    condensed_distances = scipy.spatial.distance.squareform (pairwise_distances)

    # perform clustering
    Z = scipy.cluster.hierarchy.linkage (condensed_distances)
    clusters = scipy.cluster.hierarchy.fcluster (Z, params['cluster_threshold'], 'distance')
    logging.debug ('clusters: ' + str(clusters))

    # get centers as simple mean polygon
    centers = []
    for cluster in list(set(clusters)):
        rois_cluster = [polygon2roi(x) for i, x in enumerate(polygons) if clusters[i] == cluster]
        centers.append (list( np.mean(np.array(rois_cluster), 0).astype(int) ))
    logging.debug ('centers: ' + str(centers))
    logging.debug ('out of ' + str(len(clusters)) + ' polygons left ' + str(len(centers)))

    # show clusters
    if params['debug_clustering']:
        scipy.cluster.hierarchy.dendrogram(Z)
        matplotlib.pyplot.waitforbuttonpress()
        matplotlib.pyplot.close()
    logging.debug(Z)

    return centers, clusters



def mask2bbox (mask):
    '''Extract a single (if any) bounding box from the image
    Args:
      mask:  boolean mask of the car
    Returns:
      bbox:  (x1, y1, width, height)
    '''
    assert mask is not None
    assert len(mask.shape) == 2, 'mask.shape: %s' % str(mask.shape)

    # keep only vehicles with resonable bboxes
    if np.count_nonzero(mask) == 0:
        return None

    # get bbox
    nnz_indices = np.argwhere(mask)
    if len(nnz_indices) == 0:
      return None
    (y1, x1), (y2, x2) = nnz_indices.min(0), nnz_indices.max(0) + 1 
    (height, width) = y2 - y1, x2 - x1
    return (x1, y1, width, height)



