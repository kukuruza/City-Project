import numpy as np
import cv2
import scipy.cluster.hierarchy
import matplotlib.pyplot
import sys, os, os.path as op
import logging
import setupHelper



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
    return (int((roi[0] + roi[2]) * 0.5), int((roi[1] + roi[3]) * 0.5))

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


#
# expandRoiFloat expands a ROI, and clips it within borders
#
def expandRoiFloat (roi, (imheight, imwidth), (perc_y, perc_x)):
    if (perc_y, perc_x) == (0, 0): return roi

    half_delta_y = float(roi[2] + 1 - roi[0]) * perc_y / 2
    half_delta_x = float(roi[3] + 1 - roi[1]) * perc_x / 2
    # expand each side
    roi[0] -= half_delta_y
    roi[1] -= half_delta_x
    roi[2] += half_delta_y
    roi[3] += half_delta_x
    # make integer
    roi = [int(x) for x in roi]
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
    assert (roi[0] >= 0 and roi[1] >= 0)
    assert (roi[2] <= imheight-1 and roi[3] <= imwidth-1)
    return roi


#
# expands a ROI to keep 'ratio', and maybe more, up to 'expand_perc'
#
def expandRoiToRatio (roi, (imheight, imwidth), expand_perc, ratio):
    # adjust width and height to ratio
    height = float(roi[2] + 1 - roi[0])
    width  = float(roi[3] + 1 - roi[1])
    if height / width < ratio:
       perc = ratio * width / height - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (perc, 0))
    else:
       perc = height / width / ratio - 1
       roi = expandRoiFloat (roi, (imheight, imwidth), (0, perc))
    # additional expansion
    perc = expand_perc - perc
    if perc > 0:
        roi = expandRoiFloat (roi, (imheight, imwidth), (perc, perc))
    return roi


def overlapRatio (roi1, roi2, score1, score2):
    assert (len(roi1) == 4 and len(roi2) == 4)
    dy = min(roi1[2], roi2[2]) - max(roi1[0], roi2[0])
    dx = min(roi1[3], roi2[3]) - max(roi1[1], roi2[1])
    if dy <= 0 or dx <= 0: return 0
    area1 = (roi1[2] - roi1[0]) * (roi1[3] - roi1[1])
    area2 = (roi2[2] - roi2[0]) * (roi2[3] - roi2[1])
    inters = dx * dy
    union  = area1 + area2 - inters
    logging.debug('inters: ' + str(inters) + ', union: ' +  str(union))
    assert (union >= inters and inters > 0)
    return float(inters) / union * score1 * score2


def hierarchicalClusterRoi (rois, params = {}):
    if not rois:         return [], []
    elif len(rois) == 1: return rois, [0]

    params = setupHelper.setParamUnlessThere (params, 'debug_clustering', False)
    params = setupHelper.setParamUnlessThere (params, 'scores', [1]*len(rois))

    N = len(rois)
    pairwise_distances = np.zeros((N,N), dtype = float)
    sc_in = params['scores']
    for j in range(N):
        for i in range(N):
            pairwise_distances[i][j] = 1 - overlapRatio(rois[i], rois[j], sc_in[i], sc_in[j])
    condensed_distances = scipy.spatial.distance.squareform (pairwise_distances)

    # perform clustering
    Z = scipy.cluster.hierarchy.linkage (condensed_distances)
    clusters = scipy.cluster.hierarchy.fcluster (Z, params['threshold'], 'distance')
    logging.debug('clusters: ' + str(clusters))

    # get centers as simple mean
    centers = []
    scores = []
    for cluster in list(set(clusters)):
        rois_cluster = [x for i, x in enumerate(rois) if clusters[i] == cluster]
        centers.append (list( np.mean(np.array(rois_cluster), 0).astype(int) ))
        scores_cluster = [x for i, x in enumerate(sc_in) if clusters[i] == cluster]
        scores.append (max(scores_cluster))
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

    params = setupHelper.setParamUnlessThere (params, 'debug_clustering', False)

    N = len(polygons)
    pairwise_distances = np.zeros((N,N), dtype = float)
    for j in range(N):
        for i in range(N):
            pairwise_distances[i][j] = 1 - overlapRatioPoly(polygons[i], polygons[j], params)
    condensed_distances = scipy.spatial.distance.squareform (pairwise_distances)

    # perform clustering
    Z = scipy.cluster.hierarchy.linkage (condensed_distances)
    clusters = scipy.cluster.hierarchy.fcluster (Z, params['threshold'], 'distance')
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





def readImagefile (cursor, imagefile):
    imagepath = op.join (os.getenv('CITY_DATA_PATH'), imagefile)
    if not op.exists (imagepath):
        raise Exception ('image does not exist: ' + imagepath)
    return cv2.imread(imagepath)


def createDirs (home_dir, name):
    if not op.exists(op.join(os.getenv('CITY_DATA_PATH'), home_dir)):
        raise Exception ('home_dir does not exist: ' + home_dir)
    try:        
        os.mkdir (op.join(os.getenv('CITY_DATA_PATH'), home_dir, 'Databases', name))
    except: pass
    try:
        os.mkdir (op.join(os.getenv('CITY_DATA_PATH'), home_dir, 'Images', name))
    except: pass
    try:        
        os.mkdir (op.join(os.getenv('CITY_DATA_PATH'), home_dir, 'Masks', name))
    except: pass
    try:        
        os.mkdir (op.join(os.getenv('CITY_DATA_PATH'), home_dir, 'Ghosts', name))
    except: pass


# extract homedir and folder from the somefile:
#   somefile = labelmedir / <'Images'/'Databases'/etc.> / folder / filename
#
def somefile2dirs (somefile):
    folderpath = op.dirname (somefile)
    labelmedir = op.dirname (op.dirname(folderpath))
    folder = op.basename (folderpath)
    return (labelmedir, folder)

