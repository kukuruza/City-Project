import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import logging
from learning.helperSetup import setupLogging, dbInit
from learning.dbModify    import merge, expandBboxes, filterByBorder


setupLogging ('log/learning/Merge.log', logging.INFO, 'a')

in_db_file1 = 'databases/sparse/119-Apr09-13h/angles-ghost.db'
in_db_file2 = 'databases/sparse/572-Oct28-10h/color-ghost.db'
in_db_file3 = 'databases/sparse/578-Jan22-14h/angles-ghost.db'
in_db_file4 = 'databases/sparse/578-Mar15-10h/angles-ghost.db'
in_db_file5 = 'databases/sparse/717-Apr07-15h/color-ghost.db'
in_db_file6 = 'databases/sparse/671-Mar24-12h/angles-ghost.db'
out_db_file = 'databases/sparse/all-Feb29.db'

(conn1, cursor1) = dbInit(in_db_file1, out_db_file)

(conn2, cursor2) = dbInit(in_db_file2)
merge(cursor1, cursor2)
conn2.close()
(conn2, cursor2) = dbInit(in_db_file3)
merge(cursor1, cursor2)
conn2.close()
(conn2, cursor2) = dbInit(in_db_file4)
merge(cursor1, cursor2)
conn2.close()
(conn2, cursor2) = dbInit(in_db_file5)
merge(cursor1, cursor2)
conn2.close()
(conn2, cursor2) = dbInit(in_db_file6)
merge(cursor1, cursor2)
conn2.close()

expandBboxes (cursor1)
filterByBorder (cursor1)
conn1.commit()
conn1.close()
