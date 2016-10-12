import sys, os, os.path as op
import logging
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/detector'))
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/car'))
from CarDetectorInterface import CarDetectorInterface
from Car import Car

# files of py-faster-rcnn
# FRCN_ROOT environmental variable must be set to the path of "py-faster-rcnn"
sys.path.insert(0, op.join(os.getenv('FRCN_ROOT'), 'tools'))
import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
import numpy as np
import scipy.io as sio
import caffe, os, sys


def _init_network_ (net_name, prototxt_partial_path, cpu_mode, gpu_id):

    NETS = {'vgg16': ('VGG16', 'VGG16_faster_rcnn_final.caffemodel'),
            'zf':    ('ZF', 'ZF_faster_rcnn_final.caffemodel')}

    prototxt = op.join(cfg.ROOT_DIR, 'models', NETS[net_name][0], prototxt_partial_path)
    caffemodel = op.join(cfg.ROOT_DIR, 'data', 'faster_rcnn_models', NETS[net_name][1])

    if not op.isfile(prototxt):
        raise IOError('prototxt not found at "%s"' % prototxt)
    if not op.isfile(caffemodel):
        raise IOError('caffemodel not found at "%s"' % caffemodel)

    if cpu_mode:
        logging.info ('FasterRcnnDetector: cpu mode')
        caffe.set_mode_cpu()
    else:
        logging.info ('FasterRcnnDetector: gpu mode')
        caffe.set_mode_gpu()
        caffe.set_device(gpu_id)
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    logging.info ('FasterRcnnDetector: loaded network "%s"' % caffemodel)
    return net



PASCAL20_CLASSES = ('__background__',
                'aeroplane', 'bicycle', 'bird', 'boat',
                'bottle', 'bus', 'car', 'cat', 'chair',
                'cow', 'diningtable', 'dog', 'horse',
                'motorbike', 'person', 'pottedplant',
                'sheep', 'sofa', 'train', 'tvmonitor')

class FasterRcnnDetector (CarDetectorInterface):

    def __init__ (self, net_name = 'vgg16', cpu_mode = True, gpu_id = 0, 
                  classes=PASCAL20_CLASSES):

        self.classes = classes

        self.net = _init_network_(net_name, 'faster_rcnn_alt_opt/faster_rcnn_test.pt', cpu_mode, gpu_id)

        self.CONF_THRESH = 0.7
        self.NMS_THRESH = 0.3

        cfg.TEST.HAS_RPN = True  # Use RPN for proposals
        cfg.USE_GPU_NMS = not cpu_mode;

        # layer for features
        self.features_layer = 'fc6'

        # warmup on a dummy image (only for GPU)
        if not cpu_mode:
            im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
            for i in xrange(2):
                _, _, _ = im_detect(self.net, im)

        logging.info ('FasterRcnnDetector: init performed')


    def detect (self, img):
        '''
        Given an image, detect objects and extract their features from self.features_layer
        Return
          a list of Car objects
          features in the format of numpy.array( N x Dim )

        Important note: features will be extracted BEFORE predicting bboxes
          For features after refining bboxes, call FasterRcnnExtractor.extract_features()
        '''

        # detect all object classes and regress object bounds
        scores, boxes, features_all = im_detect(self.net, img, features_layer=self.features_layer)
        logging.info ('detection had %d object proposals' % boxes.shape[0])

        # perform nms and thresholding (class by class)
        cars = []
        features = np.zeros((0, features_all.shape[1]), dtype=features_all.dtype)
        for cls_ind, cls_name in enumerate(self.CLASSES[1:]):
            cls_ind += 1 # because we skipped background
            cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
            cls_scores = scores[:, cls_ind]
            dets = np.hstack((cls_boxes,
                              cls_scores[:, np.newaxis])).astype(np.float32)
            # nms
            keep = nms(dets, self.NMS_THRESH)
            dets = dets[keep, :]
            features_cls = features_all[keep,:]

            # theshold
            keep = (dets[:,-1] >= self.CONF_THRESH)
            dets = dets[keep, :]
            features_cls = features_cls[keep,:]

            for i in range(dets.shape[0]):

                det = dets[i,:]
                roiXY = [int(x) for x in det[0:4].tolist()]
                bbox = [roiXY[0], roiXY[1], roiXY[2]-roiXY[0]+1, roiXY[3]-roiXY[1]+1]
                cars.append (Car(bbox=bbox, score=float(det[-1]), name=cls_name))

            features = np.vstack((features, features_cls))

        return cars, features


class FasterRcnnExtractor:

    def __init__ (self, net_name = 'vgg16', cpu_mode = True, gpu_id = 0):
        self.net = _init_network_(net_name, 'fast_rcnn/test.prototxt', cpu_mode, gpu_id)

        cfg.TEST.HAS_RPN = False  # Do not use RPN

        # layer for features
        self.features_layer = 'fc6'


    def extract_features (self, img, bboxes):
        '''
        Given an image and bboxes, extract their features from self.features_layer
        Input
          img: color numpy image
          bboxes: a list of bbox = [x1 y1 width height]
        Return
          features: in the format of numpy.array( N x Dim )
        '''

        # rois in py-faster-rcnn format: np.ndarray( N x 4 )
        roisXY = []
        for bbox in bboxes:
            assert isinstance(bbox, list) and len(bbox) == 4, 'bbox must be a list of 4 el.'
            bbox = [x for x in bbox]
            roisXY.append([bbox[0], bbox[1], bbox[0]+bbox[2]-1, bbox[1]+bbox[3]-1])
        roisXY = np.asarray(roisXY, dtype=int)

        _, _, features = im_detect (self.net, img, roisXY, self.features_layer)
        return features

