#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import shutil
import argparse
from random import shuffle
import numpy as np
import cv2
from learning.helperSetup import setupLogging, atcity

EXT = None
azimuth_prec = None
altitude_prec = None
azimuth_steps  = None
altitude_steps = None


def angles_grid (azimuth, altitude):
  '''Projects a pair of angles into a coarse grid. Returns the cell id'''
  assert azimuth >= 0 and azimuth < 360
  assert altitude >= 0 and altitude < 90

  azimuth_id  = int((azimuth + azimuth_prec/2) % 360 / azimuth_prec)
  altitude_id = int(altitude / altitude_prec)

  angle_id = azimuth_id * altitude_steps + altitude_id
  assert angle_id >= 0 and angle_id < azimuth_steps * altitude_steps, \
         str((angle_id, azimuth, altitude, azimuth_id, altitude_id))

  return angle_id



def copy_by_angle (in_base_dir, out_base_dir, min_vis, max_vis):
  '''Split patches into dirs by angles.
  Creates a number of dirs in out_base_dir, one per azimuth-altitude pair.'''

  # create necessary dirs
  if op.exists(atcity(out_base_dir)):
    shutil.rmtree(atcity(out_base_dir))
  os.makedirs(atcity(out_base_dir))

  # write labels file and readme-s inside each dir
  f_labels = open(atcity(op.join(out_base_dir, 'angle_labels.txt')), 'w')
  fs_readme = []
  for azimuth_id in range(azimuth_steps):
    for altitude_id in range(altitude_steps):
      azimuth  = azimuth_id  * azimuth_prec
      altitude = altitude_id * altitude_prec
      angle_id = angles_grid(azimuth, altitude)
      os.makedirs(atcity(op.join(out_base_dir, '%03d' % angle_id)))
      f_labels.write('%03d\n' % angle_id)
      readme_path = atcity(op.join(out_base_dir, '%03d' % angle_id, 'readme.txt'))
      fs_readme.append(open(readme_path, 'w'))
      fs_readme[angle_id].write('azimuth_id:  %d, range [%d, %d]\n' % 
        (azimuth_id, azimuth-azimuth_prec/2, azimuth+azimuth_prec/2))
      fs_readme[angle_id].write('altitude_id: %d, range [%d, %d]\n' % 
        (altitude_id, altitude, altitude+altitude_prec))
      fs_readme[angle_id].write('\n')
  f_labels.close()

  ids_path        = atcity(op.join(in_base_dir, 'ids.txt'))
  visibility_path = atcity(op.join(in_base_dir, 'visibility.txt'))
  angles_path     = atcity(op.join(in_base_dir, 'angles.txt'))

  # read filenames
  assert op.exists(ids_path), 'ids_path: %s' % ids_path
  with open(ids_path) as f:
    filenames = f.read().splitlines()
  n_orig = len(filenames)

  # read angles
  assert op.exists(angles_path), 'angles_path: %s' % angles_path
  with open(angles_path) as f:
    lines = f.read().splitlines()
  angles = []
  for i,line in enumerate(lines):
    words = line.split()
    assert words[0] == filenames[i]  # consistency check
    azimuth  = float(words[1])
    altitude = float(words[2])
    angles.append ((angles_grid(azimuth, altitude), azimuth, altitude))
  assert len(filenames) == len(angles)

  # filter those that do not satisfy the visibility constraints
  if op.exists(visibility_path):
    with open(visibility_path) as f:
      lines = f.read().splitlines() 
    keep_list = []
    for i,line in enumerate(lines):
      (filename, vis_str) = line.split()
      assert op.splitext(filename)[0] == filenames[i]
      if float(vis_str) >= min_vis and float(vis_str) <= max_vis:
        keep_list.append(i)

  filenames = np.asarray(filenames)[keep_list]
  angles    = np.asarray(angles)[keep_list]

  p = np.random.permutation(len(keep_list))
  filenames = filenames[p].tolist()
  angles    = angles[p].tolist()

  print 'total %d out of %d images satify visibility constraints' \
        % (len(filenames), n_orig)

  for i in range(2):
    print filenames[i], angles[i]

  # copy selected files
  for i,filename in enumerate(filenames):
    angle_id = int(angles[i][0])  # was casted to float by np.asarray
    in_filepath  = atcity (op.join(in_base_dir, '%s.%s' % (filename, EXT)))
    out_filepath = atcity (op.join(out_base_dir, '%03d' % angle_id, '%08d.%s' % (i, EXT)))
    shutil.copy (in_filepath, out_filepath)
    fs_readme[angle_id].write('azimuth: %.2f, altitude: %.2f\n' % (angles[i][1], angles[i][2]))

  for f in fs_readme:
    f.close



if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_base_dir')
  parser.add_argument('--out_base_dir')
  parser.add_argument('--logging_level', type=int, default=20)
  parser.add_argument('--min_vis', type=float, default=0)
  parser.add_argument('--max_vis', type=float, default=1)
  parser.add_argument('--azimuth_prec', type=float, default=60)
  parser.add_argument('--altitude_prec', type=float, default=15)
  parser.add_argument('--max_altitude', type=float, default=30)
  parser.add_argument('--ext', default='jpg')
  args = parser.parse_args()

  EXT = args.ext
  max_altitude   = args.max_altitude
  azimuth_prec   = args.azimuth_prec
  altitude_prec  = args.altitude_prec
  azimuth_steps  = int(360 / azimuth_prec)
  altitude_steps = int(max_altitude / altitude_prec)
  assert 360 / azimuth_prec  == int(360 / azimuth_prec),  azimuth_prec
  assert 360 / altitude_prec == int(360 / altitude_prec), altitude_prec

  copy_by_angle (args.in_base_dir, args.out_base_dir, args.min_vis, args.max_vis)
