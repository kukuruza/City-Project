import random
import unittest

from pycar import Car, saveMatCars, saveMatCar, loadMatCars
import logging
import cv2


class TestTerms (unittest.TestCase):

    def setUp(self):
        car = Car([100, 100, 110, 98])
        car.name = 'test car'
        car.yaw = 40
        car.pitch = 20
        car.patch = cv2.imread('testdata/test-patch.png')
        car.ghost = cv2.imread('testdata/test-ghost.png')
        self.car = car

    def test_save_car (self):
        saveMatCar ('testdata/test-car.mat', self.car);
        self.assertTrue(True, 'Just ok')


    def test_save_cars (self):
        cars = [self.car, self.car];
        saveMatCars ('testdata/test-cars.mat', cars);
        self.assertTrue(True, 'Just ok')


    def test_load_cars (self):
        cars = loadMatCars ('testdata/test-cars-true.mat');
        n = len(cars)
        self.assertEqual (n, 2, 'Instead of 2 cars, loaded ' + str(n))
        self.assertEqual (cars[0].bbox, [100, 100, 110, 98], 'Bad bbox')
        self.assertEqual (cars[0].name, 'test car', 'Bad name')
        self.assertEqual (cars[0].yaw, 40, 'Bad yaw')
        self.assertEqual (cars[0].pitch, 20, 'Bad pitch')
        self.assertEqual (cars[0].patch.shape, (98,110,3))
        self.assertEqual (cars[0].ghost.shape, (98,110,3))

    def test_load_empty (self):
        cars = loadMatCars ('testdata/empty-pycars.mat');
        n = len(cars)
        self.assertEqual (n, 1, 'Instead of 1 car, loaded ' + str(n))
        self.assertFalse (cars[0].bbox)




if __name__ == '__main__':
    logging.basicConfig (level=logging.CRITICAL)
    unittest.main()
