import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from learning.helperSetup import atcity, dbInit, setupLogging
from learning.helperDb import imageField
from learning.helperImg import ReaderVideo
import numpy as np
import argparse
import logging



class CityImagesDataset:
  def __init__(self, db_file, fraction=1., image_constraint='1'):

    (conn, c) = dbInit(db_file)
    c.execute('SELECT * FROM images WHERE %s ORDER BY imagefile' % image_constraint)
    self.image_entries = c.fetchall()
    conn.close()

    self.fraction = fraction
    self.image_reader = ReaderVideo()


  def _load_image(self, image_entry):
    logging.debug ('CityImagesDataset: reading %s' % 
            imageField(image_entry, 'imagefile'))
    im = self.image_reader.imread (imageField(image_entry, 'imagefile'))
    assert im is not None, image_entry
    return im


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
    num_to_use = int(len(self.image_entries) * self.fraction)
    logging.debug('CitycamDataset: will use %d frames' % num_to_use)

    image_entries = list(self.image_entries)  # make a copy
    assert len(image_entries) > 0
    if randomly: np.random.shuffle(image_entries)

    for image_entry in image_entries[:num_to_use]:
      yield self._load_image(image_entry)





if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_db_file', required=True)
  args = parser.parse_args()

  dataset = CityImagesDataset(args.in_db_file, fraction=0.01)

  for im in dataset.iterateImages(randomly=True):
    print im.shape

