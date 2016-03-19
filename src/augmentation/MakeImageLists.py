#!/usr/bin/env python
import sys, os, os.path as op
import fnmatch
import argparse
from random import shuffle
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity

def _find_files_ (directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def make_list (root_dir, name_label_pairs, out_list_name, (visibility_min, visibility_max)):
    out_list_path = op.join(root_dir, out_list_name)

    path_label_pairs = []
    line_count = 0
    for (patches_name, label) in name_label_pairs:

        visibility_path = op.join(root_dir, patches_name, 'visibility.txt')

        if op.exists(visibility_path):
            with open(visibility_path) as f:
                lines = f.read().splitlines() 
                line_count += len(lines)
                path_label_pairs += [('%s/%s' % (patches_name, line.split()[0]), label) 
                                     for line in lines 
                                     if  float(line.split()[1]) >= visibility_min
                                     and float(line.split()[1]) <= visibility_max]
        else:   # visibility file is not prsent (maybe test data)
            filepaths = _find_files_(op.join(root_dir, patches_name), '*.jpg')
            for path in filepaths:
                path = op.relpath(path, root_dir)
                path_label_pairs.append((path, label))

    shuffle(path_label_pairs)
    print 'total %d out of %d images satify visibility constraints' \
          % (len(path_label_pairs), line_count)
    print 'list %s is formed' % out_list_name

    for x in path_label_pairs[:5]:
        print x

    with open(out_list_path, 'w') as f:
        for x in path_label_pairs:
            f.write('%s %d\n' % (x[0], x[1]))



parser = argparse.ArgumentParser()
parser.add_argument('--input_list_name', required=True)
parser.add_argument('--output_list_name', required=True)
parser.add_argument('--visibility_min', type=float, default=0)
parser.add_argument('--visibility_max', type=float, default=1)
parser.add_argument('--root_dir', default='augmentation/patches')
args = parser.parse_args()

root_dir = atcity(args.root_dir)

# input_list looks like:
#    7c7c2b02ad5108fe5f9082491d52810, 0        # taxi
#    uecadcbca-a400-428d-9240-a331ac5014f6 1   # schoolbus

name_label_pairs = []
with open(op.join(root_dir, args.input_list_name)) as f:
    lines = f.read().splitlines() 
    for line in lines:
        words = line.split()
        name_label_pairs.append( (words[0], int(words[1])) )
for name_label in name_label_pairs:
    print name_label

make_list (root_dir, name_label_pairs, args.output_list_name,
           (args.visibility_min, args.visibility_max))

