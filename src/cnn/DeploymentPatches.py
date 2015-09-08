import os, sys, os.path as op
import numpy as np
import cv2
import logging
sys.path.insert(0, os.getenv('CAFFE_TOOLS'))


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
    '''
    Use this class for predicting labels or extracting features from intermediate levels.
    Currently the exact taks is regulated by the netweork architecture.
    '''

    def __init__ (self, network_path, model_path, params = {}):

        # set default values of parameters
        if not 'use_cpu' in params: params['use_cpu'] = True
        if not 'relpath' in params: params['relpath'] = os.getenv('CITY_DATA_PATH')

        # from relative to absolute paths
        network_path = op.join(params['relpath'], network_path)
        model_path   = op.join(params['relpath'], model_path)

        if not op.exists(network_path):
            raise Exception ('network file does not exit: %s' % network_path)
        if not op.exists(model_path):
            raise Exception ('model file does not exit: %s' % model_path)

        _setCaffeLoggingLevel_()    # setting the log level is before 'import caffe'
        import caffe

        if params['use_cpu']:
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


    def forward (self, patch):
        '''
        Get the result from the last layer from the forward pass.
        Expect patch to be color, 3-channels, [0,255], dtype of np.uint8
        Returns a 1-dim numpy array
        '''
        assert patch is not None
        assert patch.ndim == 3     # color image
        assert patch.shape[2] == 3  # 3-channels
        assert patch.dtype == np.dtype('uint8')

        patch = patch.astype(np.float32) / 255

        self.net.blobs['data'].data[...] = self.transformer.preprocess('data', patch)
        out = self.net.forward()

        # represent output as a 1-dim numpy array
        assert isinstance(out, dict) and len(out) == 1
        value = list(out.values())[0]
        value = value.reshape((value.size))
        
        return value


if __name__ == "__main__":
    ''' Example of usage '''

    logging.basicConfig (stream=sys.stdout, level=logging.INFO)

    network_path = 'cnn/architectures/sedan-h5-deploy-py.prototxt'
    model_path   = 'cnn/models/sedan-h5_iter_4000.caffemodel'
    deployment = DeploymentPatches (network_path, model_path)

    patch = cv2.imread(op.join(os.getenv('CITY_PATH'), 'src/cnn/testdata/sedan-40x30.png'))
    print deployment.forward(patch)
    patch = cv2.imread(op.join(os.getenv('CITY_PATH'), 'src/cnn/testdata/negative-40x30.png'))
    print deployment.forward(patch)
