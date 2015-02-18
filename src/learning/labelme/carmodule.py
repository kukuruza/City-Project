import numpy as np
import scipy.io as sio



class Car:
    def __init__ (self, bbox=[]):
        self.bbox = bbox
        self.name = ''
        self.patch = np.empty((0,0,0))
        self.ghost = np.empty((0,0,0))
        self.yaw = 0
        self.pitch = 0

    def check (self):
        (height, width, depth) = self.patch.shape
        if self.bbox == []:
            assert height == 0 and width == 0
        elif self.bbox[2] != width or self.bbox[3] != height:
            print ('bbox: ' + str(self.bbox) + ', patch: ' + str(self.patch.shape))
            assert (False)
        (height, width, depth) = self.ghost.shape
        #assert (self.bbox[0] == width and self.bbox[1] == height)
        if self.bbox == []:
            assert height == 0 and width == 0
        elif self.bbox[2] != width or self.bbox[3] != height:
            print ('bbox: ' + str(self.bbox) + ', patch: ' + str(self.ghost.shape))
            assert (False)

    def getBottomCenter (self):   # (y x)
        topRatio = 0.75
        return (self.bbox[1] + self.bbox[3] * topRatio, self.bbox[0] + self.bbox[2] / 2)

    def printout(self):
        print (self.name)
        print (self.bbox);
        if self.patch: print (img.shape)
        if self.ghost: print (img.ghost)

    def toDict (self):
        self.check()
        assert (self.name is not None)
        assert (self.bbox is not None and len(self.bbox) in [0, 4])
        assert (self.patch is not None)
        assert (self.ghost is not None)
        return {'name': self.name, 
                'bbox': self.bbox, 
                'patch': self.patch, 
                'ghost': self.ghost,
                'yaw': self.yaw,
                'pitch': self.pitch}



def saveMatCar (filepath, car):
    sio.savemat (filepath, {'car': car.toDict()})

def saveMatCars (filepath, cars, caption = None):
    assert not cars or isinstance(cars, list) and cars[0] is None or isinstance(cars[0], Car)
    cars_dict = [];
    for car in cars:
        if car is None: car = Car()
        cars_dict.append (car.toDict())
    if caption is None:
        sio.savemat (filepath, {'cars': cars_dict})
    else:
        sio.savemat (filepath, {'cars': cars_dict, 'caption': caption})

def loadMatCars (filepath):
    return sio.loadmat(filepath)
