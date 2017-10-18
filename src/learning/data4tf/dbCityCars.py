import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from learning.helperSetup import atcity, dbInit, setupLogging
from learning.helperDb import imageField, carField
from learning.helperImg import ReaderVideo
import numpy as np
import argparse
import logging


class CitycarsDataset:
  def __init__(self, db_file, fraction=1., car_constraint='1', crop_car=True,
               randomly=True):

    (conn, c) = dbInit(db_file, backup=False)
    c.execute('SELECT * FROM cars WHERE %s ORDER BY imagefile' % car_constraint)
    self.car_entries = c.fetchall()
    conn.close()

    self.fraction = fraction
    self.crop_car = crop_car
    self.image_reader = ReaderVideo()
    self.randomly = randomly


  def _load_image(self, car_entry):
    logging.debug ('CitycarsDataset: reading car %d from %s imagefile' % 
            (carField(car_entry, 'id'), carField(car_entry, 'imagefile')))
    im = self.image_reader.imread (carField(car_entry, 'imagefile'))
    if self.crop_car:
      roi = carField(car_entry, 'roi')
      car = im[roi[0]:roi[2], roi[1]:roi[3]]
    else:
      car = im
    return car


  # interface functions
  
  def __len__(self):
    return int(len(self.car_entries) * self.fraction)

  def _getitem_by_index(self, index):
    '''
    Args:
      index:   if given, returns the given index rather then
               yielding all num_to_use images from dataset
               That is used for torch.utils.data.Dataset
    '''
    car_entry = self.car_entries[index]
    return self._load_image(car_entry), car_entry

  def __getitem__(self):
    '''Yields pairs (im,gt) taken randomly from the whole dataset. 
    Used to train segmentation.
    Returns:
      im: np.uint8 array of shape [imheight, imwidth, 3]
      gt: np.uint8 array of shape [imheight, imwidth, 1]
              and values in range [0,255]
            [imheight, imwidth] are image and mask ogirinal dimensions.
    '''
    num_to_use = self.__len__()
    logging.info('CitycarsDataset: will use %d frames.' % num_to_use)

    car_entries = list(self.car_entries)  # make a copy
    if self.randomly:
      np.random.shuffle(car_entries)

    for car_entry in car_entries[:num_to_use]:
      yield self._load_image(car_entry), car_entry

    logging.info('CitycarsDataset: done with the dataset.')







if __name__ == "__main__":

  logging.basicConfig(level=logging.DEBUG, format='%(message)s')
  
  parser = argparse.ArgumentParser()
  parser.add_argument('--in_db_file', required=True)
  args = parser.parse_args()

  dataset = CitycarsDataset(args.in_db_file, fraction=0.005, randomly=False)

  print ('length', dataset.__len__())
  for im, _ in dataset.__getitem__():
    print im.shape

