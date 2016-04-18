import sys, os, os.path as op
import numpy as np
import argparse
import shutil

def merge (in_dir1, in_dir2, out_dir, in_suffix1=None, in_suffix2=None, out_suffix=None):
  names_in = ['ids', 'visibility', 'roi', 'types', 'angles']

  content = []
  names   = []
  
  # read dataset1
  if in_suffix1: in_suffix1 = '-' + in_suffix1
  for i in range(len(names_in)):
    try:  # some files may be absent, so just 'try'
      print op.join(in_dir1, '%s%s.txt' % (names_in[i], in_suffix1))
      # read file
      with open( op.join(in_dir1, '%s%s.txt' % (names_in[i], in_suffix1)) ) as f:
        lines = f.read().splitlines()
      # change the first column of the file
      lines = [' '.join([op.join(op.relpath(in_dir1, out_dir), line.split()[0])] + line.split()[1:]) for line in lines]
      # append
      content.append( lines )
      names.append( names_in[i] )
    except:
      print ('dir1: %s, did not find file %s' % (in_dir1, names_in[i]))

  # read dataset2
  if in_suffix2: in_suffix2 = '-' + in_suffix2
  for i in range(len(names)):
    try:  # some files may be absent, so just 'try'
      print op.join(in_dir2, '%s%s.txt' % (names[i], in_suffix2))
      # read file
      with open( op.join(in_dir2, '%s%s.txt' % (names[i], in_suffix2)) ) as f:
        lines = f.read().splitlines()
      # change the first column of the file
      lines = [' '.join([op.join(op.relpath(in_dir2, out_dir), line.split()[0])] + line.split()[1:]) for line in lines]
      # append
      content[i] += lines
    except:
      print ('dir2: %s, did not find file %s' % (in_dir2, names_in[i]))

#  print content[0]

  # shuffle dataset
  #if not content:
  #  return
  num = len(content[0])
  p = np.random.permutation(num)
  for i in range(len(content)):
    content[i] = np.asarray(content[i])[p].tolist()

  # write dataset
  if op.exists(out_dir):
    print 'removing %s' % out_dir
    shutil.rmtree(out_dir)
  os.makedirs(out_dir)

  if out_suffix: out_suffix = '-' + out_suffix
  for i in range(len(names)):
    with open(op.join(out_dir, '%s%s.txt' % (names[i], out_suffix)), 'w') as f:
      f.write('\n'.join(content[i]))


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_dir1', required=True, help='NOT relative to CITY_DATA_PATH')
  parser.add_argument('--in_dir2', required=True, help='NOT relative to CITY_DATA_PATH')
  parser.add_argument('--out_dir', required=True, help='NOT relative to CITY_DATA_PATH')
  parser.add_argument('--in_suffix1', default='')
  parser.add_argument('--in_suffix2', default='')
  parser.add_argument('--out_suffix', default='')
  args = parser.parse_args()

  merge (args.in_dir1, args.in_dir2, args.out_dir, 
         args.in_suffix1, args.in_suffix2, args.out_suffix)
