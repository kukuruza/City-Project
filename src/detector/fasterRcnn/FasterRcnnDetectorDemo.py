import logging
import sys, os, os.path as op
import numpy as np
import cv2
import json
from FasterRcnnDetector import FasterRcnnDetector
import matplotlib.pyplot as plt
from utils.timer import Timer
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/car'))
from Car import Car



def vis_detections(im, cars):
    """Draw detected bounding boxes."""

    im = im[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(im, aspect='equal')
    for car in cars:
        bbox = car.bbox
        score = car.score
        name = car.name

        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]), bbox[2], bbox[3],
                          fill=False,
                          edgecolor='red', linewidth=3.5)
            )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=14, color='white')

    plt.axis('off')
    plt.tight_layout()
    plt.draw()
    plt.show()


if __name__ == '__main__':
    ''' demo with a sample image'''

    # input
    model_dir = 'vgg16'
    image_path  = '../testdata/image00001.png'

    # init
    logging.basicConfig (level=logging.INFO)
    im = cv2.imread(image_path)
    detector = FasterRcnnDetector (model_dir, cpu_mode = True)
    detector.CONF_THRESH = 0.5


    # work
    timer = Timer()
    timer.tic()
    cars = detector.detect(im)
    timer.toc()
    print 'detection took %.3f sec' % timer.total_time

    print 'got %d detections' % len(cars)

    # visualize detections for each class
    for car in cars:
        print car.bbox, car.score, car.name
    vis_detections(im, cars)
