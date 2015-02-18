import random
import unittest

import carmodule
import logging
import cv2


class TestTerms (unittest.TestCase):

    def setUp(self):
        car = carmodule.Car([100, 100, 110, 98])
        car.name = 'test car'
        car.yaw = 40
        car.pitch = 20
        car.patch = cv2.imread('testdata/test-patch.png')
        car.ghost = cv2.imread('testdata/test-ghost.png')
        self.car = car

    def test_save_car (self):
        carmodule.saveMatCar ('testdata/test-car.mat', self.car);
        self.assertTrue(True, 'Just ok')


    def test_save_cars (self):
        cars = [self.car, self.car];
        carmodule.saveMatCars ('testdata/test-cars.mat', cars);
        self.assertTrue(True, 'Just ok')


if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()
