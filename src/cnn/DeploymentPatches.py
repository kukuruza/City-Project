import os, sys, os.path as op
import numpy as np
import cv2
sys.path.insert(0, os.getenv('CAFFE_TOOLS'))
import logging


def _setCaffeLoggingLevel_ ():
    # level     python value    caffe value
    # DEBUG      10              0 (default)
    # INFO       20              1
    # WARNING    30 (default)    2
    # ERROR      40              3
    level_python = logging.getLogger().getEffectiveLevel()
    level_caffe  = '%d' % (level_python / 10 - 1)
    os.environ['GLOG_minloglevel'] = level_caffe



class DeploymentPatches:

    def __init__ (self, network_path, model_path, use_cpu = True):

        _setCaffeLoggingLevel_()
        import caffe    # 'import caffe' is after setting the log level

        if not op.exists(network_path):
            raise Exception ('network file does not exit: %s' % network_path)
        if not op.exists(model_path):
            raise Exception ('model file does not exit: %s' % model_path)

        if use_cpu:
            caffe.set_mode_cpu()
        else:
            caffe.set_mode_gpu()

        self.net = caffe.Net(network_path, model_path, caffe.TEST)

        self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        #
        # switch dimensions to match Ch x H x W
        self.transformer.set_transpose('data', (2,0,1))
        #
        # set_mean_value should be necessary! I don't know the correct results are without it
        #self.transformer.set_mean_value('data', 0.5)
        #
        # Flip channels takes place because model is trained aand expects OpenCV representation of BGR.
        #   However, caffe.io.load_image() uses skimage.img_as_float() to load image as RGB.
        # In our case, this class is called by our python scripts which use opencv ot load images.
        #   That means we don't need to flip channels
        #self.transformer.set_channel_swap('data', (2,1,0))

        logging.info ('network initialized')

    def classify (self, patch):
        '''
        Expect patch to be color, 3-channels, [0,255], dtype of np.uint8
        '''
        assert patch is not None
        assert patch.ndim == 3     # color image
        assert patch.shape[2] == 3  # 3-channels
        assert patch.dtype == np.dtype('uint8')

        patch = patch.astype(np.float32) / 255

        self.net.blobs['data'].data[...] = self.transformer.preprocess('data', patch)
        out = self.net.forward()
        return int(out['output'][0][0][0][0])


if __name__ == "__main__":

    logging.basicConfig (stream=sys.stdout, level=logging.INFO)

    network_path = op.join(os.getenv('CITY_DATA_PATH'), 'cnn/architectures/hdf5-sedan-deploy-py.prototxt')
    model_path   = op.join(os.getenv('CITY_DATA_PATH'), 'cnn/models/hdf5-sedan_iter_4000.caffemodel')
    deployment = DeploymentPatches (network_path, model_path, use_cpu = True)

    import re
    png_dir = op.join(os.getenv('CITY_DATA_PATH'), 'patches/try-hdf5/testing-40x30')
    png_names = [ f for f in os.listdir(png_dir) if re.search('(.png)$', f) ]

    with open(op.join(os.getenv('CITY_DATA_PATH'), 'patches/try-hdf5/predicted-py.txt'), 'w') as f:
        for png_name in png_names:
            png_path = op.join(png_dir, png_name)

            patch = cv2.imread(png_path)
            label = deployment.classify(patch)

            f.write ('%d\n' % label)

    # patch = cv2.imread(op.join(os.getenv('CITY_PATH'), 'src/cnn/testdata/car-40x30.png'))
    # label = deployment.classify(patch)
    # patch = cv2.imread(op.join(os.getenv('CITY_PATH'), 'src/cnn/testdata/taxi-40x30.png'))
    # label = deployment.classify(patch)
    # patch = cv2.imread(op.join(os.getenv('CITY_PATH'), 'src/cnn/testdata/negative-40x30.png'))
    # label = deployment.classify(patch)
    # patch = cv2.imread(op.join(os.getenv('CITY_PATH'), 'src/cnn/testdata/negative-40x30-2.png'))
    # label = deployment.classify(patch)
