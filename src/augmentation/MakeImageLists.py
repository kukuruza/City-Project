#!/usr/bin/env python
import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
import fnmatch
import argparse
import numpy as np
from random import shuffle
from helperSetup import atcity

def _find_files_ (directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def make_list (root_dir, name_label_pairs, out_list_name, (vis_min, vis_max)):
    out_list_path = op.join(root_dir, out_list_name)

    entries = []
    line_count = 0
    for (patches_name, label) in name_label_pairs:

        ids_path        = op.join(root_dir, patches_name, 'ids.txt')
        visibility_path = op.join(root_dir, patches_name, 'visibility.txt')
        roi_path        = op.join(root_dir, patches_name, 'roi.txt')

        # read filenames
        assert op.exists(ids_path), 'ids_path: %s' % ids_path
        with open(ids_path) as f:
          filenames = f.read().splitlines()
        filenames = [filename.split()[0] for filename in filenames]  # ignore second col.
        filenames = [op.splitext(filename)[0] for filename in filenames]  # ignore ext.
        line_count += len(filenames)

        # read roi-s if present
        if op.exists(roi_path):
          with open(roi_path) as f:
            lines = f.read().splitlines()
          roi_strs = []
          for i,line in enumerate(lines):
            words = line.split()
            assert filenames[i] == op.splitext(words[0])[0]
            roi_strs.append(' '.join(words[1:]))
        else:
          roi_strs = ['NA NA NA NA'] * len(filenames)

        # create mask names
        maskfiles = []
        for filename in filenames:
          # mask name is 'scene/000001m.png' for filename 'scene/000001p'
          if filename[-1] == 'p':   # until a new MakePatches
            maskname = op.join(op.dirname(filename), '%sm' % op.basename(filename[:-1]))
          else:
            maskname = op.join(op.dirname(filename), '%s' % op.basename(filename))
          if not op.exists(op.join(root_dir, patches_name, '%s.png' % maskname)):
            maskfile = 'NA'
          else:
            maskfile = op.join(patches_name, maskname)
          maskfiles.append(maskfile)

        # write sub_entries list
        sub_entries = []
        for i,filename in enumerate(filenames):
          entry = '%s %s %s %s' % (op.join(patches_name, filename), 
                                   label, 
                                   roi_strs[i], 
                                   maskfiles[i])
          sub_entries.append(entry)

        # filter those that do not satisfy the visibility constraints
        if op.exists(visibility_path):
          with open(visibility_path) as f:
            lines = f.read().splitlines() 
          keep_list = []
          for i,line in enumerate(lines):
            (filename, vis_str) = line.split()
            assert op.splitext(filename)[0] == filenames[i]
            if float(vis_str) >= vis_min and float(vis_str) <= vis_max:
              keep_list.append(i)
          sub_entries = np.asarray(sub_entries)[keep_list].tolist()

        entries += sub_entries

    shuffle(entries)
    print 'total %d out of %d images satify visibility constraints' \
          % (len(entries), line_count)
    print 'list %s is formed' % out_list_name

    for x in entries[:5]:
        print x

    with open(out_list_path, 'w') as f:
      f.write('\n'.join(entries) + '\n')



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_list_name', required=True)
    parser.add_argument('--output_list_name', required=True)
    parser.add_argument('--min_visibility', type=float, default=0)
    parser.add_argument('--max_visibility', type=float, default=1)
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
               (args.min_visibility, args.max_visibility))

