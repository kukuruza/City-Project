import sqlite3
import logging
import argparse

if __name__ == "__main__":

  parser = argparse.ArgumentParser('Takes properties from CAD db, '
     'combines them into a single string, and writes to 2D db. '
     'It is assumed that "name" field of 2D db is actually a "model_id" of 3D db.')
  parser.add_argument('--cad_db_path', required=True)
  parser.add_argument('--db_path', required=True)
  parser.add_argument('--logging', type=int, default=20, choices=[10,20,30,40])
  parser.add_argument('--classes', nargs='+', required=True, 
      help='Names of classes to in clas table')
  parser.add_argument('--dry_run', action='store_true')
  args = parser.parse_args()

  logging.basicConfig(level=args.logging, format='%(levelname)s: %(message)s')
  #progressbar.streams.wrap_stderr()

  cad_conn = sqlite3.connect(args.cad_db_path)
  cad_cursor = cad_conn.cursor()

  conn = sqlite3.connect(args.db_path)
  cursor = conn.cursor()

  cursor.execute('SELECT DISTINCT(name) FROM cars')
  model_ids = cursor.fetchall()
  for model_id, in model_ids:
    values = []
    for class_ in args.classes:
      cad_cursor.execute('SELECT label FROM clas WHERE model_id=? AND class=?', (model_id, class_))
      value = cad_cursor.fetchone()
      value = value[0] if value is not None else ''
      logging.debug('model_id %s has value "%s" for class "%s"' % (model_id, value, class_))
      values.append(value)
    values = ', '.join(values)
    if len(values) == 0:
      values = None  # Should be no empty values.
    logging.debug('model_id %s will update the name to "%s"' % (model_id, values))
    cursor.execute('UPDATE cars SET name=? WHERE name=?', (values, model_id))

  if not args.dry_run:
    conn.commit()
  conn.close()
  cad_conn.close()
