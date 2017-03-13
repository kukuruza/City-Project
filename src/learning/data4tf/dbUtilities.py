def iterate_frame_batches(dataset, batch_size, image_size, 
                          color_mean_bgr=[128,128,128], randomly=False):
  '''Yields batches of clips.
  Args:
    dataset -- a class from read_dataset.py
  Yields:
    images -- np.float32 [batch_size, image_size[0], image_size[1], 3)]
  '''
  dtype = np.float32

  im_batch = np.zeros((batch_size,image_size,image_size,3), dtype)

  # read frame by frames. Each BATCH_SIZE yields a batch
  iim = 0
  for iim, im in enumerate(dataset.iterate_frames(randomly=randomly)):
    
    # process each frame and put it into a batch
    im = cv2.resize(im, (image_size,image_size))
    im = im.astype(dtype)
    im = (im.astype(dtype) - color_mean_bgr) / 255.0
    im_batch[iim % batch_size, ...] = im

    if (iim + 1) % batch_size == 0:
      logging.debug('iterate_frame_batches: next batch of shape %s' % str(im_batch.shape))
      yield im_batch

  assert (iim+1)/batch_size > 0, 'batch_generator did not make any frames'
  logging.debug('batch_generator: got %d frames and %d batches' %
                ((iim+1), (iim+1)/batch_size))


