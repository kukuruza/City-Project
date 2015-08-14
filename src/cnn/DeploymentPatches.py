import os, sys, os.path as op
import numpy as np
import cv2
import caffe

class DeploymentPatches:

    def __init__ (self, network_path, model_path, scaled_training = False, gpu_mode = False):
        
        if not op.exists(network_path):
            raise Exception ('network file does not exit: %s' % network_path)
        if not op.exists(model_path):
            raise Exception ('model file does not exit: %s' % model_path)

        if gpu_mode:
	    caffe.set_mode_gpu()
        else:
	    caffe.set_mode_cpu()

        self.net = caffe.Net(network_path, model_path, caffe.TEST)

	self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        self.transformer.set_transpose('data', (2,0,1))
	if not scaled_training:
	    self.transformer.set_raw_scale('data', 255)  # reference model operates on [0,255] range instead of [0,1]

        # Flip channels takes place because model is trained aand expects OpenCV representation of BGR.
	#   However, caffe.io.load_image() uses skimage.img_as_float() to load image as RGB.
	# In our case, this class is called by our python scripts which use opencv ot load images.
	#   That means we don't need to flip channels
	#self.transformer.set_channel_swap('data', (2,1,0))  # the reference model has channels in BGR instead of RGB

	# TODO: forward the stdout to a file during init

    def classify (self, patch):
	'''
	Expect patch to be color, 3-channels, [0,255], dtype of np.uint32
	'''
	assert patch.ndim == 3     # color image
	assert patch.shape[2] == 3  # 3-channels
	assert patch.dtype == np.dtype('uint8')

	patch = patch.astype(np.float32) / 255
	
	self.net.blobs['data'].data[...] = self.transformer.preprocess('data', patch)
	out = self.net.forward()
	print("Predicted class is #{}.".format(out['prob'].argmax()))

if __name__ == "__main__":
    network_path = '../examples/city/deploy_python.prototxt'
    model_path = '../examples/city/city_quick_iter_4000.caffemodel'
    deployment = DeploymentPatches(network_path, model_path)
    patch = cv2.imread('../examples/images/car.png')
    deployment.classify(patch)
