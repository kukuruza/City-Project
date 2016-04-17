import sys, os, os.path as op
import numpy as np
import argparse

def split (in_dir, setname_fraction_pairs):
  '''setname_fraction_pairs - list of tuple (setname, fraction)
       setname is the name of a subset, e.g. 'train', 'eval', 'test'
       fraction is the percantage of the dataset to go there
  '''
  names_in = ['ids', 'visibility', 'roi', 'types', 'angles']
  
  # read dataset
  content = []
  names   = []
  for i in range(len(names_in)):
    try:  # some files may be absent, so just 'try'
      print op.join(in_dir, '%s.txt' % names_in[i])
      with open( op.join(in_dir, '%s.txt' % names_in[i]) ) as f:
        content.append( f.read().splitlines() )
      names.append( names_in[i] )
    except:
      print ('did not find file %s' % names_in[i])

  # shuffle dataset
  if not content:
    return
  num = len(content[0])
  p = np.random.permutation(num)
  for i in range(len(content)):
    content[i] = np.asarray(content[i])[p].tolist()

  # split dataset
  higher = 0
  for setname, fraction in setname_fraction_pairs:
    # update dataset boundaries
    lower = higher
    higher = lower + int(num * fraction)
    assert higher <= num
    # write a portion of dataset to each file
    for i in range(len(names)):
      with open( op.join(in_dir, '%s-%s.txt' % (names[i], setname)), 'w' ) as f:
        f.write('\n'.join(content[i][lower:higher]))

    
if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--in_dir', required=True, help='NOT relative to CITY_DATA_PATH')
  parser.add_argument('--setnames', nargs='+')
  parser.add_argument('--fractions', nargs='+', type=float)
  args = parser.parse_args()

  assert len(args.setnames) == len(args.fractions)
  setname_fraction_pairs = []
  for i in range(len(args.setnames)):
    print (args.setnames[i], args.fractions[i])
    setname_fraction_pairs.append( (args.setnames[i], args.fractions[i]) )

  split (args.in_dir, setname_fraction_pairs)
