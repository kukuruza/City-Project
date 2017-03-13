import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from learning.helperSetup import atcity, dbInit, setupLogging
from learning.helperDb import imageField, carField
from learning.helperImg import ReaderVideo
import numpy as np
import argparse
import logging



class CitycarsDataset:
  def __init__(self, db_file, fraction=1., car_constraint='1'):

    (conn, c) = dbInit(db_file)
    c.execute('SELECT * FROM cars WHERE %s ORDER BY imagefile' % car_constraint)
    self.car_entries = c.fetchall()
    conn.close()

    self.fraction = fraction
    self.image_reader = ReaderVideo()


  def _load_image(self, car_entry):
    logging.debug ('CitycarsDataset: reading car %d from %s imagefile' % 
            (carField(car_entry, 'id'), carField(car_entry, 'imagefile')))
    im = self.image_reader.imread (carField(car_entry, 'imagefile'))
    roi = carField(car_entry, 'roi')
    car = im[roi[0]:roi[2], roi[1]:roi[3]]
    return car


  # interface functions


  def iterateImages(self, randomly=True):
    '''Yields pairs (im,gt) taken randomly from the whole dataset. 
    Used to train segmentation.
    Returns:
      im: np.uint8 array of shape [imheight, imwidth, 3]
      gt: np.uint8 array of shape [imheight, imwidth, 1]
              and values in range [0,255]
            [imheight, imwidth] are image and mask ogirinal dimensions.
    '''
    num_to_use = int(len(self.car_entries) * self.fraction)
    logging.debug('CitycamDataset: will use %d frames' % num_to_use)

    car_entries = list(self.car_entries)  # make a copy
    if randomly: np.random.shuffle(car_entries)

    for car_entry in car_entries[:num_to_use]:
      yield self._load_image(car_entry)





if __name__ == "__main__":

  logging.basicConfig(level=logging.DEBUG, format='%(message)s')
  
  parser = argparse.ArgumentParser()
  parser.add_argument('--in_db_file', required=True)
  args = parser.parse_args()

  dataset = CitycarsDataset(args.in_db_file, fraction=0.002)

  for im in dataset.iterateImages(randomly=False):
    print im.shape

