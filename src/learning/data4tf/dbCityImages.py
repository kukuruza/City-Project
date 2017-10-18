import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
from learning.helperSetup import atcity, dbInit, setupLogging
from learning.helperDb import imageField
from learning.helperImg import ReaderVideo
import numpy as np
import argparse
import logging



class CityimagesDataset:
  def __init__(self, db_file, fraction=1., image_constraint='1', randomly=True):

    (conn, c) = dbInit(db_file)
    c.execute('SELECT * FROM images WHERE %s ORDER BY imagefile' % image_constraint)
    self.image_entries = c.fetchall()
    conn.close()

    self.fraction = fraction
    self.image_reader = ReaderVideo()
    self.randomly = randomly

    self.pos = 0  # Position for __getitem__.

  def _load_image(self, image_entry):
    logging.debug ('CityImagesDataset: reading %s' % 
            imageField(image_entry, 'imagefile'))
    im = self.image_reader.imread (imageField(image_entry, 'imagefile'))
    assert im is not None, image_entry
    return im

  # interface functions
  
  def __len__(self):
    return int(len(self.image_entries) * self.fraction)

  def _getitem_by_index(self, index):
    '''
    Args:
      index:   if given, returns the given index rather then
               yielding all num_to_use images from dataset
               That is used for torch.utils.data.Dataset
    '''
    image_entry = self.image_entries[index]
    return self._load_image(image_entry)

  def __getitem__(self):
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
    if self.randomly: np.random.shuffle(image_entries)

    for image_entry in image_entries[:num_to_use]:
      yield self._load_image(image_entry)

  def _get_batch(self, imsize, batchsize):
    assert type(imsize) is list or type(imsize) is tuple, imsize
    assert len(imsize) == 2, imsize
    batch = None
    for i, image in enumerate(self.dataset.__getitem__()):
      image = imresize(image, imsize)
      if batch is None:
        batch = np.zeros([batchsize] + list(image.shape), float)
      batch[i % batchsize] = image
      if (i-1) % batchsize == 0:
        logging.debug(batch.shape)
        yield batch





if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_db_file', required=True)
  args = parser.parse_args()

  dataset = CityimagesDataset(args.in_db_file, fraction=0.01)

  im = dataset._getitem_by_index(1)
  print im.shape

  for im in dataset.__getitem__():
    print im.shape

