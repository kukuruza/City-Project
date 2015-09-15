import os, sys
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src/learning'))
import random
import logging
import sqlite3
import unittest
import helperTesting
from dbModify import *
import helperImg
import helperKeys


class TestEmptyDb (unittest.TestCase):
    ''' Test that functions don't break on empty databases '''

    def setUp (self):
        self.conn = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDb (self.conn)

    def tearDown (self):
        self.conn.close()


    def test_filterByBorder (self):
        c = self.conn.cursor()
        filterByBorder (c, {})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_filterByRatio (self):
        c = self.conn.cursor()
        filterByRatio (c, {})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_filterBySize (self):
        c = self.conn.cursor()
        filterBySize (c, {'size_map_path': 'testdata/mapSize.tiff', 'relpath': '.'})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_thresholdScore (self):
        c = self.conn.cursor()
        thresholdScore (c, params = {})
        c.execute('SELECT COUNT(*) FROM cars')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_clusterBboxes (self):
        c = self.conn.cursor()
        clusterBboxes (c, params = {})
        c.execute('SELECT COUNT(*) FROM cars')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_expandBboxes (self):
        ''' Make sure it runs '''
        c = self.conn.cursor()
        expandBboxes (c, params = {})

    def test_assignOrientations (self):
        ''' Make sure it runs '''
        c = self.conn.cursor()
        assignOrientations (c, {'size_map_path': 'testdata/mapSize.tiff',
                                'yaw_map_path': 'testdata/mapYaw.tiff',
                                'pitch_map_path': 'testdata/mapPitch.tiff', 
                                'relpath': '.'})

    def test_merge (self):
        c = self.conn.cursor()
        merge(c, c)
        c.execute('SELECT COUNT(*) FROM cars')
        self.assertEqual (c.fetchone()[0], 0)
        c.execute('SELECT COUNT(*) FROM images')
        self.assertEqual (c.fetchone()[0], 0)
        c.execute('SELECT COUNT(*) FROM matches')
        self.assertEqual (c.fetchone()[0], 0)
        



class TestMicroDb (helperTesting.TestMicroDbBase):
    
    def setUp (self):
        super(TestMicroDb, self).setUp()

    def _makeDebugParams_ (self, sequence):
        ''' convenience helper function '''
        params = {}
        params['debug'] = True
        params['image_processor'] = helperImg.ProcessorRandom({'dims': (100,100)})
        params['key_reader'] = helperKeys.KeyReaderSequence(sequence)
        return params

    # filterByBorder

    def test_filterByBorder_defaults (self):
        ''' Check default parameters. None of the cars is close to border '''
        c = self.conn.cursor()
        filterByBorder (c, {})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 3)

    def test_filterByBorder_loose (self):
        ''' Increased border_thresh_perc to filter out 2 out of 3 cars '''
        c = self.conn.cursor()
        filterByBorder (c, {'border_thresh_perc': 0.3})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 1)

    def test_filterByBorder_loose_constraint (self):
        ''' Constraint to filter out only 'trucks', with very tight border_thresh_perc==1. '''
        c = self.conn.cursor()
        params = {'border_thresh_perc': 1, 'constraint': 'name == "truck"'}
        filterByBorder (c, params)
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 1)

    def test_filterByBorder_debug_all (self):
        filterByBorder (self.conn.cursor(), self._makeDebugParams_([32, 32, 32]))
        
    def test_filterByBorder_debug_several (self):
        filterByBorder (self.conn.cursor(), self._makeDebugParams_([32, 27, 32]))
        
    # filterByRatio

    def test_filterByRatio_loose (self):
        ''' Very loose ratio_acceptance keeps all the cars, even with bad target_ratio. '''
        c = self.conn.cursor()
        filterByRatio (c, {'target_ratio': 5, 'ratio_acceptance': 1.001})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 3)

    def test_filterByRatio_targetRatio (self):
        ''' Impossible target_ratio leaves no cars '''
        c = self.conn.cursor()
        filterByRatio (c, {'target_ratio': 100})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_filterByRatio_ratioAcceptance (self):
        ''' Very tight ratio_acceptance. Only img1.car2 matches target_ratio exactly. '''
        c = self.conn.cursor()
        filterByRatio (c, {'ratio_acceptance': 100})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 1)

    def test_filterByRatio_constraint (self):
        ''' Only cars from the 1st image are filtered out. '''
        c = self.conn.cursor()
        filterByRatio (c, {'target_ratio': 10, 'constraint': 'imagefile == "img1"'})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 1)

    def test_filterByRatio_debug_all (self):
        filterByRatio (self.conn.cursor(), self._makeDebugParams_([32, 32, 32]))
        
    def test_filterByRatio_debug_several (self):
        filterByRatio (self.conn.cursor(), self._makeDebugParams_([32, 27]))
        
    # filterBySize

    def test_filterBySize_defaults (self):
        ''' The map is 20 almost everywhere. Two cars are close to that. '''
        c = self.conn.cursor()
        filterBySize (c, {'size_map_path': 'testdata/mapSize.tiff', 'relpath': '.', 
                          'min_width': 0, 'size_acceptance': 2})
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        # c.execute('SELECT score FROM cars')
        # for (score,) in c.fetchall(): print score
        self.assertEqual (numLeft, 2)

    def test_filterBySize_tight (self):
        ''' Run tight size_acceptance. '''
        c = self.conn.cursor()
        params = {'size_map_path': 'testdata/mapSize.tiff', 'relpath': '.', 
                  'size_acceptance': 100, 'min_width': 0}
        filterBySize (c, params)
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_filterBySize_loose (self):
        ''' Run loose size_acceptance. '''
        c = self.conn.cursor()
        params = {'size_map_path': 'testdata/mapSize.tiff', 'relpath': '.', 
                  'size_acceptance': 1.01, 'min_width': 0}
        filterBySize (c, params)
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 3)

    def test_filterBySize_minWidth (self):
        ''' loose size_acceptance won't make a difference, but 'min_width' will filter out the small car. '''
        c = self.conn.cursor()
        params = {'size_map_path': 'testdata/mapSize.tiff', 'relpath': '.',
                  'size_acceptance': 1.01, 'min_width': 10}
        filterBySize (c, params)
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 2)

    def test_filterBySize_constraint (self):
        ''' 'size_acceptance' is very tight, so only cars from the 1st image are filtered out. '''
        c = self.conn.cursor()
        params = {'size_map_path': 'testdata/mapSize.tiff', 'relpath': '.', 
                  'size_acceptance': 100, 
                  'min_width': 10, 
                  'constraint': 'imagefile == "img1"'}
        filterBySize (c, params)
        c.execute('SELECT COUNT(*) FROM cars WHERE score > 0.5')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 1)

    def test_filterBySize_debug_all (self):
        params = self._makeDebugParams_([32, 32, 32])
        params['size_map_path'] = 'testdata/mapSize.tiff'
        params['relpath'] = '.'
        filterBySize (self.conn.cursor(), params)
        
    def test_filterBySize_debug_several (self):
        params = self._makeDebugParams_([32, 27])
        params['size_map_path'] = 'testdata/mapSize.tiff'
        params['relpath'] = '.'
        filterBySize (self.conn.cursor(), params)
        
    # thresholdScore

    def test_thresholdScore_loose (self):
        ''' Low 'score_threshold' keeps all cars '''
        c = self.conn.cursor()
        thresholdScore (c, params = {'score_threshold': 0.5})
        c.execute('SELECT COUNT(*) FROM cars')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 3)

    def test_thresholdScore_tight (self):
        ''' High 'score_threshold' filters out all cars '''
        c = self.conn.cursor()
        thresholdScore (c, params = {'score_threshold': 1.5})
        c.execute('SELECT COUNT(*) FROM cars')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 0)

    def test_thresholdScore_medium (self):
        ''' Cars in img1 are set low score, so they are filtered out by average 'score_threshold' '''
        c = self.conn.cursor()
        c.execute('UPDATE cars SET score=? WHERE imagefile=?', (0, 'img1'))
        thresholdScore (c, params = {'score_threshold': 0.5})
        c.execute('SELECT COUNT(*) FROM cars')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 1)

    # expandBboxes

    def test_expandBboxes_noRatio (self):
        ''' Expand each side by 100%. Don't keep the ratio.
            Original carid0=(6,6), carid1=(20,15), carid2=(16,16) '''
        c = self.conn.cursor()
        expandBboxes (c, params = {'expand_perc': 1, 'keep_ratio': False})
        c.execute('SELECT width,height FROM cars WHERE id = 1')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (12,12))
        c.execute('SELECT width,height FROM cars WHERE id = 2')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (40,30))
        c.execute('SELECT width,height FROM cars WHERE id = 3')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (32,32))

    def test_expandBboxes_4to3Ratio (self):
        ''' Expand each side by 100%. Keep the ratio to default height:width = 3:4.
            Original carid0=(6,6), carid1=(20,15), carid2=(16,16) '''
        c = self.conn.cursor()
        expandBboxes (c, params = {'expand_perc': 1, 'keep_ratio': True, 'target_ratio': 0.75})
        c.execute('SELECT width,height FROM cars WHERE id = 1')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (12,9))
        c.execute('SELECT width,height FROM cars WHERE id = 2')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (40,30))
        c.execute('SELECT width,height FROM cars WHERE id = 3')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (32,24))

    def test_expandBboxes_1to1Ratio (self):
        ''' Expand each side by 100%. Keep the ratio to 1:1.
            Original carid0=(6,6), carid1=(20,15), carid2=(16,16) '''
        c = self.conn.cursor()
        expandBboxes (c, params = {'expand_perc': 1, 'keep_ratio': True, 'target_ratio': 1})
        c.execute('SELECT width,height FROM cars WHERE id = 1')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (12,12))
        c.execute('SELECT width,height FROM cars WHERE id = 2')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (30,30))
        c.execute('SELECT width,height FROM cars WHERE id = 3')
        (width,height) = c.fetchone()
        self.assertEqual ((width,height), (32,32))

    def test_expandBboxes_debug_all (self):
        expandBboxes (self.conn.cursor(), self._makeDebugParams_(6*[32])) # one per car and one per image
        
    def test_expandBboxes_debug_several (self):
        expandBboxes (self.conn.cursor(), self._makeDebugParams_([32, 27]))
        

    # clusterBboxes

    def test_clusterBboxes_tight (self):
        ''' Tight 'cluster_threshold' won't let intersecting car1 and car2 get merged. '''
        c = self.conn.cursor()
        clusterBboxes (c, {'cluster_threshold': 0})
        c.execute('SELECT COUNT(*) FROM cars')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 3)

    def test_clusterBboxes_loose (self):
        ''' Loose 'cluster_threshold' merges intersecting car1 and car2. '''
        c = self.conn.cursor()
        clusterBboxes (c, {'cluster_threshold': 1000})
        c.execute('SELECT COUNT(*) FROM cars')
        (numLeft,) = c.fetchone()
        self.assertEqual (numLeft, 2)

    def test_clusterBboxes_debug_all (self):
        clusterBboxes (self.conn.cursor(), self._makeDebugParams_([32, 32, 32]))
        
    def test_clusterBboxes_debug_several (self):
        clusterBboxes (self.conn.cursor(), self._makeDebugParams_([32, 27]))

    # assignOrientations

    def test_assignOrientations (self):
        ''' Make sure it runs '''
        c = self.conn.cursor()
        assignOrientations (c, {'size_map_path': 'testdata/mapSize.tiff',
                                'yaw_map_path': 'testdata/mapYaw.tiff',
                                'pitch_map_path': 'testdata/mapPitch.tiff',
                                'relpath': '.'})
        c.execute('SELECT yaw FROM cars')
        yaw_entries = c.fetchall()
        c.execute('SELECT pitch FROM cars')
        pitch_entries = c.fetchall()
        self.assertEqual (yaw_entries[0][0], -69)
        self.assertEqual (yaw_entries[1][0], 140)
        self.assertEqual (yaw_entries[2][0], -69)
        for (pitch,) in pitch_entries:
            self.assertEqual (pitch, 51)

    # merge

    def test_merge_same (self):
        c = self.conn.cursor()
        merge(c, c)
        # cars
        c.execute('SELECT name,x1 FROM cars')
        car_entries = c.fetchall()
        self.assertEqual (len(car_entries), 6)
        self.assertEqual (car_entries[0], ('sedan', 24))
        self.assertEqual (car_entries[1], ('truck', 44))
        self.assertEqual (car_entries[2], ('truck', 24))
        self.assertEqual (car_entries[3], ('sedan', 24))
        self.assertEqual (car_entries[4], ('truck', 44))
        self.assertEqual (car_entries[5], ('truck', 24))
        # images
        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()
        self.assertEqual (len(image_entries), 3) # duplicate images
        self.assertEqual (image_entries[0], ('img1',))
        self.assertEqual (image_entries[1], ('img2',))
        self.assertEqual (image_entries[2], ('img3',))
        #c.execute('SELECT id,carid,match FROM matches')
        #match_entries = c.fetchall()
        #self.assertEqual (len(match_entries), 6)

    def test_merge_addEmpty (self):
        # create and empty db
        conn_empty = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDb (conn_empty)
        cursor_empty = conn_empty.cursor()
        # merge
        c = self.conn.cursor()
        merge(c, cursor_empty)
        # cars
        c.execute('SELECT name,x1 FROM cars')
        car_entries = c.fetchall()
        self.assertEqual (len(car_entries), 3)
        # images
        c.execute('SELECT imagefile FROM images')
        image_entries = c.fetchall()
        self.assertEqual (len(image_entries), 3)
        # # matches
        # c.execute('SELECT id,carid,match FROM matches')
        # match_entries = c.fetchall()
        # self.assertEqual (len(match_entries), 3)
        # close
        conn_empty.close()

    def test_merge_toEmpty (self):
        # create and empty db
        conn_empty = sqlite3.connect(':memory:')  # in RAM
        helperDb.createDb (conn_empty)
        cursor_empty = conn_empty.cursor()
        # merge
        c = self.conn.cursor()
        merge(cursor_empty, c)
        # cars
        c.execute('SELECT name,x1 FROM cars')
        car_entries = c.fetchall()
        self.assertEqual (len(car_entries), 3)
        self.assertEqual (car_entries[0], ('sedan', 24))
        self.assertEqual (car_entries[1], ('truck', 44))
        self.assertEqual (car_entries[2], ('truck', 24))
        # images
        c.execute('SELECT imagefile,src FROM images')
        image_entries = c.fetchall()
        self.assertEqual (len(image_entries), 3)
        self.assertEqual (image_entries[0], ('img1','src'))
        self.assertEqual (image_entries[1], ('img2','src'))
        self.assertEqual (image_entries[2], ('img3','src'))
        # matches
        c.execute('''SELECT imagefile,name FROM cars WHERE id IN 
                    (SELECT carid FROM matches WHERE match == 2)''')
        match_entries = c.fetchall()
        self.assertEqual (len(match_entries), 2)
        self.assertEqual (match_entries[0], ('img1','truck'))
        self.assertEqual (match_entries[1], ('img2','truck'))
        # close
        conn_empty.close()



if __name__ == '__main__':
    logging.basicConfig (level=logging.ERROR)
    unittest.main()
