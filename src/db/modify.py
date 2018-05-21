#! /usr/bin/env python
import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
import argparse
from db.lib.helperSetup import dbInit
from db.lib import dbFilter, dbModify, dbManual, dbInfo, dbExport, dbLabel, dbEvaluate, dbLabelme
from augmentation import dbCadFilter
import progressbar


parser = argparse.ArgumentParser(description=
  '''Open existing database, modify it with different tools,
  and optionally save the result in another database.
  Positional arguments describe available tools.
  Each tool has its own options, run a tool with -h flag
  to show its options. You can use tool one after the other in a pipe.
  ''')
parser.add_argument('-i', '--in_db_file', required=False,
    help='If specified, open this file. If unspecified create out_db_file.')
parser.add_argument('-o', '--out_db_file', required=False,
    help='Unspecified output file assumes a dry run.')
parser.add_argument('--relpath', required=False,
    help='if specified, consider "imagefile" entries relative to this dir.')
parser.add_argument('--logging', default=20, type=int, choices={10, 20, 30, 40},
    help='Log debug (10), info (20), warning (30), error (40).')
subparsers = parser.add_subparsers()
dbFilter.add_parsers(subparsers)
dbModify.add_parsers(subparsers)
dbManual.add_parsers(subparsers)
dbInfo.add_parsers(subparsers)
dbExport.add_parsers(subparsers)
dbCadFilter.add_parsers(subparsers)
dbLabel.add_parsers(subparsers)
dbEvaluate.add_parsers(subparsers)
dbLabelme.add_parsers(subparsers)
# Add a dummy option to allow passing '--' in order to end lists.
dummy = subparsers.add_parser('--')
dummy.set_defaults(func=lambda *args: None)


# Parse main parser and the first subsparser.
args, rest = parser.parse_known_args(sys.argv[1:])
out_db_file = args.out_db_file

progressbar.streams.wrap_stderr()
logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')
(conn, cursor) = dbInit(args.in_db_file, args.out_db_file)

# Iterate tools.
args.func(cursor, args)
while rest:
  args, rest = parser.parse_known_args(rest)
  args.func(cursor, args)

if out_db_file is not None:
  conn.commit()
conn.close()

