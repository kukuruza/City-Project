
import random
import unittest

from clustering import queryCars, clusterCarsIntoGhosts
import logging
import cv2
import os.path


class TestQuery (unittest.TestCase):

    def test_return_type(self):
        self.index = queryCars (data_paths_list=['testdata/test-*s.mat'])
        self.assertTrue (isinstance(self.index, list))
        self.assertEqual (len(self.index), 1)
        self.assertEqual (len(self.index[0][1]), 2)

    def test_name(self):
        self.index = queryCars (data_paths_list=['testdata/test-*s.mat'],
                                filters={'name': 'test car'})
        self.assertEqual (len(self.index), 1)
        self.assertEqual (len(self.index[0][1]), 2)

    def test_none_name(self):
        self.index = queryCars (data_paths_list=['testdata/test-*s.mat'],
                                filters={'name.equal': 'bad name'})
        self.assertEqual (len(self.index), 0)

    def test_pitch(self):
        self.index = queryCars (data_paths_list=['testdata/test-*s.mat'],
                                filters={'pitch.min': 0, 'pitch.max': 90})
        self.assertEqual (len(self.index), 1)
        self.assertEqual (len(self.index[0][1]), 2)

    def test_one_yaw(self):
        self.index = queryCars (data_paths_list=['testdata/test-*s.mat'],
                                filters={'yaw.min': 0})
        self.assertEqual (len(self.index), 1)
        self.assertEqual (len(self.index[0][1]), 1)

    def test_returned_value(self):
        self.index = queryCars (data_paths_list=['testdata/test-*s.mat'])
        self.assertEqual (len(self.index), 1)
        self.assertEqual (len(self.index[0][1]), 2)
        # test that the returned values are strings and their paths exist
        self.assertTrue (isinstance(self.index[0][0], str))
        self.assertTrue (os.path.exists(self.index[0][0]))
        self.assertEqual (self.index[0][1][0], 0)
        self.assertEqual (self.index[0][1][1], 1)



class TestClustering (unittest.TestCase):

    def test_car_vs_bus(self):

        # load data list
        import os.path as OP
        data_list_path = 'testdata/test-data.list'
        if not os.path.exists(data_list_path):
            raise Exception('data_list_path does not exist: ' + data_list_path)
        data_list_file = open(data_list_path, 'r')
        data_list = data_list_file.read().split('\n')
        data_list_file.close()
        # remove empty lines
        data_list = filter(None, data_list)
        # make it relative to the data_list_path
        data_list = [OP.join(OP.dirname(data_list_path), x) for x in data_list]

        logging.basicConfig (level=logging.INFO)
        counters = clusterCarsIntoGhosts (data_list,
                                          'testdata/test-clusters.json', 
                                          'testdata/clusters')
        self.assertEqual (len(counters), 2)
        self.assertTrue ('cluster1' in counters)
        self.assertTrue ('cluster2' in counters)
        self.assertEqual (counters['cluster1'], 2)
        self.assertEqual (counters['cluster2'], 0)





if __name__ == '__main__':
    unittest.main()
