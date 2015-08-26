import random
import unittest
import sqlite3
import helperDb


def makeMicroDbVer2 ():
    ''' Make a db of OLD that is used in many test cases '''
    conn = sqlite3.connect(':memory:')  # in RAM
    helperDb.createDb(conn)
    c = conn.cursor()

    s = 'images(imagefile,width,height,src,maskfile,time)'
    v = ('img1',100,100,'src','mask1','2015-08-21 01:01:01.000')
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, v)
    v = ('img2',100,100,'src','mask2','2015-08-21 01:01:02.000')
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, v)
    v = ('img3',100,100,'src','mask3','2015-08-21 01:01:03.000')
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?)' % s, v)

    s = 'cars(id,imagefile,name,x1,y1,width,height,score,yaw,pitch,color)'
    v = (1,'img1','sedan',24,42,6,6,1,180,45,'blue')
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?,?)' % s, v)
    v = (2,'img1','truck',44,52,20,15,1,None,None,None)  # default ratio
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?,?)' % s, v)
    v = (3,'img2','truck',24,42,16,16,1,None,None,None)
    c.execute('INSERT INTO %s VALUES (?,?,?,?,?,?,?,?,?,?,?)' % s, v)

    s = 'matches(id,carid,match)'
    # match1: car1, match2: car2 and car3
    c.execute('INSERT INTO %s VALUES (?,?,?)' % s, (1,1,1))
    c.execute('INSERT INTO %s VALUES (?,?,?)' % s, (2,2,2))
    c.execute('INSERT INTO %s VALUES (?,?,?)' % s, (3,3,2))
    
    return conn


class TestMicroDbBase (unittest.TestCase):

    def setUp (self):
        self.conn = makeMicroDbVer2()

    def tearDown (self):
        self.conn.close()
