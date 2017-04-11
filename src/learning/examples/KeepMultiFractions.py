#! /usr/bin/env python
import os, sys, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify    import keepFraction


parser = argparse.ArgumentParser()
parser.add_argument('--in_db_file', required=True)
parser.add_argument('--dry_run', action='store_true')
parser.add_argument('--out_nums', nargs='+', required=True, type=int,
                    help='Number of images to keep for each output dir.')
parser.add_argument('--logging_level', default=20, type=int)
args = parser.parse_args()

setupLogging ('log/learning/KeepFraction.log', args.logging_level, 'a')

out_db_dir  = op.dirname(args.in_db_file)

letters_count = {}

for out_num in args.out_nums:
  # number of images
  numstr = '%dK' % (out_num / 1000) if out_num % 1000 == 0 else out_num
  # letter
  if out_num not in letters_count:
    letters_count[out_num] = 1
    letter = ''
  else:
    letters_count[out_num] += 1
    letter = '-%d' % letters_count[out_num]
  # in_db_name
  in_db_name = op.basename(op.splitext(args.in_db_file)[0])
  # out_db_file
  out_db_name = '%s-n%s%s' % (in_db_name, numstr, letter)
  out_db_file = op.join(out_db_dir, '%s.db' % out_db_name)
  logging.info('out_num %d, out_db_file: %s' % (out_num, out_db_file))

  if not args.dry_run:
    (conn, cursor) = dbInit (args.in_db_file, out_db_file)
    keepFraction(cursor, keep_num=out_num, randomly=True)
    conn.commit()
    conn.close()

