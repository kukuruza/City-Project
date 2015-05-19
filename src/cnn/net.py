import numpy as np
import sys
import csv
import os
from sys import argv
from os.path import basename

caffe_python = os.getenv('PYTHONPATH')
sys.path.insert(0, caffe_python)

import caffe


class Net:

    def __init__(self, model_file, pretrained, mean, cpu=True,
                 image_dims=( 40, 30), raw_scale=255, channel_swap=(2, 1, 0)):
        self.net = caffe.Classifier(model_file, pretrained,
                                    image_dims=image_dims,
                                    raw_scale=raw_scale,
                                    channel_swap=channel_swap,
                                    mean=mean)
        #if cpu:
        #    self.net.set_mode_cpu()
        #else:
        #    self.net.set_mode_gpu()

        #self.net.set_phase_test()

    def predict(self, caffe_images):
        predictions = self.net.predict(caffe_images)
        return [predict.argmax() for predict in predictions]

    def predictions(self, images):
        predicts = []
        count = len(images)
        i = 1
        for img_batch in chunks(images, 10):
            caffe_imgs = [caffe.io.load_image(img) for img in img_batch]
            labels = self.predict(caffe_imgs)

            print("{0}/{1}".format(i*10, count))
            i += 1

            img_names = [basename(img).split('.')[0] for img in img_batch]
            predicts += zip(img_names, labels)
        return sorted(predicts, reverse=False, key=lambda x: int(x[0]))


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def save_to_file(filename, arr):
    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(arr)


def kaggle(model_file, pretrained, mean, imgs_basepath, save_filename):
    mean = np.load(mean)
   # print('mean.shape:  ' + str(mean.shape))
    net = Net(model_file, pretrained, mean)

    import glob
    image_files = glob.glob (os.path.join(imgs_basepath, '*.png'))
    #print (image_files)

    #basepath = "{0}/test_24x18".format(imgs_basepath)
    #image_files = ["{0}/{1}".format(basepath, filename) for filename in os.listdir(basepath)]

    result = [['Image_Name', 'Digit']] + net.predictions(image_files)
    save_to_file(save_filename, result)

# 40000
# model_file='winny_deploy.prototxt', pretrained='iter_51000.caffemodel',
# mean='mean.npy', imgs_basepath=/opt/SVHN
if __name__ == '__main__':
    model_file = argv[1]
    pretrained = argv[2]
    mean = argv[3]
    imgs_basepath = argv[4]
    save_filename = argv[5]

    kaggle(model_file, pretrained, mean, imgs_basepath, save_filename)
