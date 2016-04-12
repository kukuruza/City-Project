#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import shutil
import argparse
from random import shuffle
import numpy as np
from learning.helperSetup import setupLogging, atcity

EXT = 'png'


# def split_by_angle (in_base_dir, out_dir):

#   if op.exists(atcity(out_dir)):
#     shutil.rmtree(atcity(out_dir))
#   os.makedirs(atcity(out_dir))

#   ids_path        = op.join(in_base_dir, 'ids.txt')
#   visibility_path = op.join(in_base_dir, 'visibility.txt')
#   angles_path     = op.join(in_base_dir, 'angles.txt')

#   # read filenames
#   assert op.exists(ids_path), 'ids_path: %s' % ids_path
#   with open(ids_path) as f:
#     filenames = f.read().splitlines()
#   line_count += len(filenames)

#   # read angles
#   assert op.exists(angles_path), 'angles_path: %s' % angles_path
#   with open(angles_path) as f:
#     lines = f.read().splitlines()
#   for i,line in enumerate(lines):
#     words = line.split()
#     assert words[0] == filenames[i]  # consistency check
#     azimuth  = float(words[1])
#     altitude = float(words[2])



#   # write sub_entries list
#   sub_entries = []
#   for i,filename in enumerate(filenames):
#     entry = '%s %s %s %s' % (op.join(patches_name, filename), 
#                              label, 
#                              roi_strs[i], 
#                              maskfiles[i])
#     sub_entries.append(entry)

#   # filter those that do not satisfy the visibility constraints
#   if op.exists(visibility_path):
#     with open(visibility_path) as f:
#       lines = f.read().splitlines() 
#     keep_list = []
#     for i,line in enumerate(lines):
#       (filename, vis_str) = line.split()
#       assert op.splitext(filename)[0] == filenames[i]
#       if float(vis_str) >= vis_min and float(vis_str) <= vis_max:
#         keep_list.append(i)
#     sub_entries = np.asarray(sub_entries)[keep_list].tolist()

#   entries += sub_entries



#   shuffle(entries)
#   print 'total %d out of %d images satify visibility constraints' \
#         % (len(entries), line_count)
#   print 'list %s is formed' % out_list_name

#   for x in entries[:5]:
#       print x

#   with open(out_list_path, 'w') as f:
#     f.write('\n'.join(entries) + '\n')


#   i = 0
#   for in_filepath in _find_files (atcity(in_base_dir), '*.jpg'):
#     in_filepath = 
#     out_filepath = op.join (atcity(out_dir), '%08d.jpg' % i)
#     shutil.copy (in_filepath, out_filepath)
#     i += 1



def copy_label_dir (in_base_dir, out_dir, min_vis, max_vis):

  if op.exists(atcity(out_dir)):
    shutil.rmtree(atcity(out_dir))
  os.makedirs(atcity(out_dir))

  ids_path        = atcity(op.join(in_base_dir, 'ids.txt'))
  visibility_path = atcity(op.join(in_base_dir, 'visibility.txt'))

  # read filenames
  assert op.exists(ids_path), 'ids_path: %s' % ids_path
  with open(ids_path) as f:
    filenames = f.read().splitlines()
  n_orig = len(filenames)

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

  filenames = np.asarray(filenames)[keep_list].tolist()
  shuffle(filenames)

  print 'total %d out of %d images satify visibility constraints' \
        % (len(filenames), n_orig)

  for x in filenames[:5]:
    print x

  # copy selected files
  for i,filename in enumerate(filenames):
    in_filepath  = op.join (atcity(in_base_dir), '%s.%s' % (filename, EXT))
    out_filepath = op.join (atcity(out_dir), '%08d.%s' % (i, EXT))
    shutil.copy (in_filepath, out_filepath)



if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_base_dir')
  parser.add_argument('--out_dir')
  parser.add_argument('--logging_level', type=int, default=20)
  parser.add_argument('--min_vis', type=float, default=0)
  parser.add_argument('--max_vis', type=float, default=1)
  args = parser.parse_args()

  copy_label_dir (args.in_base_dir, args.out_dir, args.min_vis, args.max_vis)
