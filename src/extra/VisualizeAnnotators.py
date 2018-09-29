''' Visualize how many images have been annotated '''

from glob import glob
import os, os.path as op
import argparse
import logging
import numpy as np
import matplotlib.pyplot as plt


def read_list_file(path):
  if not op.exists(path):
    raise Exception('File does not exist: %s' % path)
  with open(path) as f:
    lines = f.read().splitlines()
  lines = [op.splitext(op.basename(x))[0] for x in lines]
  lines = [op.splitext(x)[0] for x in lines]  # Sometimes labelme produces and extra dot.
  elements = [int(x) for x in lines]  # To make it easier with numpy.
  logging.info('File %s has %d entries' % (path, len(elements)))

  name = op.splitext(op.basename(path))[0]
  return elements, name


def process(lists_and_names):
  assert len(lists_and_names) > 1

  # The first list should have all the elements that appear in other lists.
  main_list, main_name = lists_and_names[0]
  X = np.arange(len(main_list))
  logging.info('Total %d elements' % X.size)

  fig, axarr = plt.subplots(len(lists_and_names)-1, sharex=True)
  plt.subplots_adjust(hspace=0.4)

  Y_accum = np.zeros(shape=X.shape, dtype=int)

  # Make the corresponding "present" list for each of lists_and_names[1:]
  for ilist, (list_, name) in enumerate(lists_and_names[1:]):
    Y = np.in1d(main_list, list_)
    Y_accum += Y.astype(int)
    axarr[ilist].plot(X, Y)
    axarr[ilist].set_title(name, loc='left')
    axarr[ilist].spines['top'].set_visible(False)
    axarr[ilist].spines['bottom'].set_visible(False)
    axarr[ilist].spines['left'].set_visible(False)
    axarr[ilist].spines['right'].set_visible(False)
    axarr[ilist].get_yaxis().set_visible(False)

  print ('At least two annotations: %d out of %d images.' % ((Y_accum > 1).sum(), Y_accum.size))

  plt.show()
  fig.patch.set_visible(False)


  

if __name__ == "__main__":

  parser = argparse.ArgumentParser('Do one of the automatic operations on a db.')
  parser.add_argument('--list_paths', nargs='+', required=True)
  parser.add_argument('--logging', type=int, default=20)
  parser.add_argument('--display', action='store_true')
  args = parser.parse_args()

  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')

  process([read_list_file(path) for path in args.list_paths])