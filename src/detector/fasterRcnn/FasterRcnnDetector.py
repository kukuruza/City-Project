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


class FasterRcnnDetector (CarDetectorInterface):

    def __init__ (self, net_name = 'vgg16', cpu_mode = True, gpu_id = 0):

        self.CLASSES = ('__background__',
                        'aeroplane', 'bicycle', 'bird', 'boat',
                        'bottle', 'bus', 'car', 'cat', 'chair',
                        'cow', 'diningtable', 'dog', 'horse',
                        'motorbike', 'person', 'pottedplant',
                        'sheep', 'sofa', 'train', 'tvmonitor')

        self.NETS = {'vgg16': ('VGG16', 'VGG16_faster_rcnn_final.caffemodel'),
                     'zf':    ('ZF', 'ZF_faster_rcnn_final.caffemodel')}

        self.CONF_THRESH = 0.7
        self.NMS_THRESH = 0.3

        cfg.TEST.HAS_RPN = True  # Use RPN for proposals
        cfg.USE_GPU_NMS = not cpu_mode;

        prototxt = op.join(cfg.ROOT_DIR, 'models', self.NETS[net_name][0],
                                'faster_rcnn_alt_opt', 'faster_rcnn_test.pt')
        caffemodel = op.join(cfg.ROOT_DIR, 'data', 'faster_rcnn_models',
                                  self.NETS[net_name][1])

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
        self.net = caffe.Net(prototxt, caffemodel, caffe.TEST)

        logging.info ('FasterRcnnDetector: loaded network "%s"' % caffemodel)

        # warmup on a dummy image (only for GPU)
        if not cpu_mode:
            im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
            for i in xrange(2):
                _, _= im_detect(self.net, im)

        logging.info ('FasterRcnnDetector: init performed')


    def detect (self, img):

        # detect all object classes and regress object bounds
        scores, boxes = im_detect(self.net, img)
        logging.info ('detection had %d object proposals' % boxes.shape[0])

        # perform nms and thresholding
        cars = []
        for cls_ind, cls_name in enumerate(self.CLASSES[1:]):
            cls_ind += 1 # because we skipped background
            cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
            cls_scores = scores[:, cls_ind]
            dets = np.hstack((cls_boxes,
                              cls_scores[:, np.newaxis])).astype(np.float32)
            # nms
            keep = nms(dets, self.NMS_THRESH)
            dets = dets[keep, :]

            for det in dets:

                # threshold by score
                if det[-1] >= self.CONF_THRESH:
                    roiXY = [int(x) for x in det[0:4].tolist()]
                    bbox = [roiXY[0], roiXY[1], roiXY[2]-roiXY[0]+1, roiXY[3]-roiXY[1]+1]
                    cars.append (Car(bbox=bbox, score=float(det[-1]), name=cls_name))

        return cars
