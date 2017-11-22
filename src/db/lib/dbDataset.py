import sys, os, os.path as op
from helperSetup import atcity, dbInit, setupLogging
from helperDb import imageField, carField
from helperImg import ReaderVideo
import numpy as np
from scipy.misc import imresize
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


  def __len__(self):
    if self.fraction == 1:
      return len(self.image_entries)  # No rounding errors.
    else:
      return int(len(self.image_entries) * self.fraction)


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


  def getitem_by_index(self, index):
    image_entry = self.image_entries[index]
    return self._load_image(image_entry)


  def get_batch(self, imsize, batchsize):
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


class CitycarsDataset:
  def __init__(self, db_file, fraction=1., car_constraint='1', crop_car=True,
               randomly=True):

    (conn, c) = dbInit(db_file)
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


  def __len__(self):
    return int(len(self.car_entries) * self.fraction)


  def __getitem__(self):
    '''Yields pairs (im,gt) taken randomly from the whole dataset. 
    Yields:
      im: np.uint8 array of shape [imheight, imwidth, 3]
      gt: car_entry
    '''
    num_to_use = self.__len__()
    logging.debug('CitycarsDataset: will use %d frames.' % num_to_use)

    car_entries = list(self.car_entries)  # make a copy
    if self.randomly:
      np.random.shuffle(car_entries)

    for car_entry in car_entries[:num_to_use]:
      yield self._load_image(car_entry), car_entry

    logging.debug('CitycarsDataset: done with the dataset.')


  def _getitem_by_index(self, index):
    '''
    Args:
      index:   if given, returns the given index rather then
               yielding all num_to_use images from dataset
               That is used for torch.utils.data.Dataset
    '''
    car_entry = self.car_entries[index]
    return self._load_image(car_entry), car_entry


  def get_batch(self, imsize, batchsize):
    assert type(imsize) is list or type(imsize) is tuple, imsize
    assert len(imsize) == 2, imsize
    batch_image = None
    batch_car_entry = [None] * batchsize
    for i, (image, car_entry) in enumerate(self.__getitem__()):
      image = imresize(image, imsize)
      if batch_image is None:
        batch_image = np.zeros([batchsize] + list(image.shape), float)
      batch_image[i % batchsize] = image
      batch_car_entry[i % batchsize] = car_entry
      if (i+1) % batchsize == 0:
        logging.debug(batch_image.shape)
        yield batch_image, batch_car_entry


class CitymatchesDataset:
  ''' Dataset for getting tuples of matched car patches. '''

  def __init__(self, db_file, fraction=1., crop_car=True, randomly=True):

    (conn, c) = dbInit(db_file)

    # TODO: do all of this in my SQL request
    c.execute('''SELECT DISTINCT(match) FROM matches
                 GROUP BY match HAVING COUNT(*) > 1''')
    matches = c.fetchall()
    self.matched_car_entries = []
    for match, in matches:
      c.execute('''SELECT * FROM cars WHERE id IN 
                   (SELECT carid FROM matches WHERE match = ?)''', (match,))
      car_entries = c.fetchall()
      assert len(car_entries) >= 2
      self.matched_car_entries.append(car_entries)

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


  def __len__(self):
    return int(len(self.matched_car_entries) * self.fraction)


  def __getitem__(self):
    '''Yields tuples of matched pairs ((im,gt), (im,gt), ...).
    Matches are smapled randomly throughout the database.
    Yields:
      im: np.uint8 array of shape [imheight, imwidth, 3]
      gt: car_entry
    '''
    num_to_use = len(self)
    logging.debug('CitymatchesDataset: will use %d matches.' % num_to_use)

    if self.randomly:
      np.random.shuffle(self.matched_car_entries)

    for cars_tuple in self.matched_car_entries[:num_to_use]:
      yield [(self._load_image(car_entry), car_entry) for car_entry in cars_tuple]

    logging.debug('CitycarsDataset: done with the dataset.')


  def _getitem_by_index(self, index):
    '''
    Args:
      index:   if given, returns the given index rather then
               yielding all num_to_use images from dataset
               That is used for torch.utils.data.Dataset
    '''
    cars_tuple = self.matched_car_entries[index]
    return [(self._load_image(car_entry), car_entry) for car_entry in cars_tuple]


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--in_db_file', required=True)
  parser.add_argument('--dataset_type', required=True,
      choices=['images', 'cars', 'matches'])
  args = parser.parse_args()

  if args.dataset_type == 'images':
    dataset = CityimagesDataset(args.in_db_file, fraction=0.01)
    im,  = dataset.getitem_by_index(1)
    print im.shape
    for im in dataset.__getitem__():
        print im.shape

  elif args.dataset_type == 'cars':
    dataset = CitycarsDataset(args.in_db_file, fraction=0.005, randomly=False)
    for im, car_entry in dataset.__getitem__():
      print im.shape

  elif args.dataset_type == 'matches':
    dataset = CitymatchesDataset(args.in_db_file, fraction=0.005, randomly=False)
    print ('length', len(dataset))
    for matched_cars in dataset.__getitem__():
      print (' ')
      for im, car_entry in matched_cars:
        print im.shape, car_entry
