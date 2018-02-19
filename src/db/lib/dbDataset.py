''' Pytorch dataset binding to our .db data. '''

import sys, os, os.path as op
from helperSetup import atcity, dbInit, setupLogging
from helperDb import imageField, carField
from helperImg import ReaderVideo
import numpy as np
from scipy.misc import imresize
import argparse
import logging
from torch.utils.data import Dataset


class CityimagesDataset(Dataset):
  def __init__(self, db_file, image_constraint='1', car_constraint='1', use_maps=False):
    from torch.utils.data import Dataset

    (self.conn, self.c) = dbInit(db_file)
    self.c.execute('SELECT * FROM images WHERE %s ORDER BY imagefile' % image_constraint)
    self.image_entries = self.c.fetchall()

    self.image_reader = ReaderVideo()
    self.car_constraint = car_constraint

    self.use_maps = use_maps
    if use_maps:
        from scenes.lib.cache import MapsCache
        self.sizemap_cache = MapsCache('pose_size')
        self.pitchmap_cache = MapsCache('pose_pitch')
        #self.azimuth_cache = MapsCache('pose_azimuth')

  def close(self):
    self.conn.close()

  def _load_image(self, image_entry):
    logging.debug ('CityImagesDataset: reading %s' % 
            imageField(image_entry, 'imagefile'))
    im = self.image_reader.imread (imageField(image_entry, 'imagefile'))
    if imageField(image_entry, 'maskfile') is None:
      mask = None
    else:
      mask = self.image_reader.maskread (imageField(image_entry, 'maskfile'))
    assert im is not None, image_entry
    assert len(im.shape) == 3 and im.shape[2] == 3, 'Change code for non 3-channel.'
    im = im[:,:,::-1]   # BGR to RGB.
    return im, mask

  def __len__(self):
    return len(self.image_entries)

  def __getitem__(self, index):
    '''Used to train detection/segmentation.
    Returns:
      im:     np.uint8 array of shape [imheight, imwidth, 3]
      gt:     np.uint8 array of shape [imheight, imwidth, 1]
              and values in range [0,255], where
              [imheight, imwidth] are image and mask ogirinal dimensions.
      boxes:  np.int32 array of shape [4]
    '''
    image_entry = self.image_entries[index]
    im, mask = self._load_image(image_entry)

    imagefile = imageField(image_entry, 'imagefile')

    s = 'SELECT x1,y1,width,height FROM cars WHERE imagefile="%s" AND (%s)' % (imagefile, self.car_constraint)
    logging.debug('dbDataset request: %s' % s)
    self.c.execute(s)
    bboxes = self.c.fetchall()

    item = {'image': im, 'mask': mask, 'bboxes': bboxes, 'imagefile': imagefile}

    if self.use_maps:
        item['sizemap'] = self.sizemap_cache[imagefile]
        item['pitchmap'] = self.pitchmap_cache[imagefile]
        #azimuthmap = self.azimuthmap_cache[imagefile]
        # FIXME: What to do with azimuth - bin it?

    return item


class CitycarsDataset:
  '''
  One item is one car, rather than image with multiple cars.
  Car can be cropped.
  '''
  def __init__(self, db_file, fraction=1., car_constraint='1', crop_car=True,
               randomly=True, with_mask=False):

    (self.conn, self.c) = dbInit(db_file)
    self.c.execute('SELECT * FROM cars WHERE %s ORDER BY imagefile' % car_constraint)
    self.car_entries = self.c.fetchall()

    self.fraction = fraction
    self.crop_car = crop_car
    self.image_reader = ReaderVideo()
    self.randomly = randomly
    self.with_mask = with_mask


  def close(self):
    self.conn.close()
    

  def _load_image(self, car_entry):
    logging.debug ('CitycarsDataset: reading car %d from %s imagefile' % 
            (carField(car_entry, 'id'), carField(car_entry, 'imagefile')))
    im = self.image_reader.imread (carField(car_entry, 'imagefile'))
    if self.with_mask:
      imagefile = carField(car_entry, 'imagefile')
      self.c.execute('SELECT maskfile FROM images WHERE imagefile=?', (imagefile,))
      maskfile = self.c.fetchone()[0]
      if maskfile is None:
        mask = None
      else:
        mask = self.image_reader.maskread(maskfile)
    else:
      mask = None
    assert len(im.shape) == 3 and im.shape[2] == 3, 'Change code for non 3-channel.'
    im = im[:,:,::-1]   # BGR to RGB.
    if self.crop_car:
      roi = carField(car_entry, 'roi')
      im = im[roi[0]:roi[2], roi[1]:roi[3]]
      mask = mask[roi[0]:roi[2], roi[1]:roi[3]] if mask is not None else None
    return {'image': im, 'mask': mask, 'entry': car_entry}


  def __len__(self):
    return int(len(self.car_entries) * self.fraction)


  def __getitem__(self, index):
    '''
    Returns:
      im: np.uint8 array of shape [imheight, imwidth, 3]
      gt: car_entry
    '''
    car_entry = self.car_entries[index]
    return self._load_image(car_entry)



class CitymatchesDataset:
  ''' Dataset for getting tuples of matched car patches. '''

  def __init__(self, db_file, fraction=1., crop_car=True, randomly=True):

    (conn, c) = dbInit(db_file)

    # TODO: Implement mask return.
    # TODO: do all of this in my SQL request (because of mask, maybe move cycle to _load_image)
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
    assert len(im.shape) == 3 and im.shape[2] == 3, 'Change code for non 3-channel.'
    im = im[:,:,::-1]   # BGR to RGB.
    if self.crop_car:
      roi = carField(car_entry, 'roi')
      im = im[roi[0]:roi[2], roi[1]:roi[3]]
    return {'image': im, 'entry': car_entry}


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
      yield [self._load_image(car_entry) for car_entry in cars_tuple]

    logging.debug('CitycarsDataset: done with the dataset.')


  def __getitem__(self, index):
    '''
    Args:
      index:   if given, returns the given index rather then
               yielding all num_to_use images from dataset
               That is used for torch.utils.data.Dataset
    '''
    cars_tuple = self.matched_car_entries[index]
    return [self._load_image(car_entry) for car_entry in cars_tuple]


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--in_db_file', required=True)
  parser.add_argument('--dataset_type', required=True,
      choices=['images', 'cars', 'matches'])
  args = parser.parse_args()

  if args.dataset_type == 'images':
    dataset = CityimagesDataset(args.in_db_file, fraction=0.01)
    im, _ = dataset.__getitem__(1)
    print im.shape

  elif args.dataset_type == 'cars':
    dataset = CitycarsDataset(args.in_db_file, fraction=0.005, randomly=False)
    im, car_entry = dataset.__getitem__(1)
    print im.shape

  elif args.dataset_type == 'matches':
    dataset = CitymatchesDataset(args.in_db_file, fraction=0.005, randomly=False)
    print ('length', len(dataset))
    matched_cars = dataset.__getitem__(1)
    for im, car_entry in matched_cars:
      print im.shape, car_entry

