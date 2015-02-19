#!/usr/bin/python
#
# Clustering aims to prepare Car/PyCar objects collected from different sources
#   into dataset that can be used for training/testing.
#
# The input of the module is collections of cars, the output is folders 
#   with patches that meet specified requirements (e.g. orientation.)
#
# Clustering cars based by orientation/size/type/color is set by user.
# The sources of objects are set in a config files.
# Format of output dataset can be different for different packages.
# Maybe splitting into training/testing can be done here.
#

IMAGE_EXT = '.png'


import logging
import os, sys
import os.path as OP
import shutil
import glob
import json
import numpy, cv2

if not os.environ.get('CITY_PATH'):
    print 'First set the environmental variable CITY_PATH'
    sys.exit()
else:
    sys.path.insert(0, OP.join(os.getenv('CITY_PATH'), 'src'))

from pycar.pycar import Car, loadMatCars


def parseFilterName (filter_name):
    # lack of dot means 'equal'
    numdots = filter_name.count('.')
    if numdots == 0: 
        filter_name = filter_name + '.equal'
    elif numdots > 1:
        raise Exception('filter "' + filter_name + '" has more than one dot')
    filter_parts = filter_name.split('.')
    assert len(filter_parts) == 2

    # check operations
    filter_key = filter_parts[0]
    filter_op = filter_parts[1]
    if filter_op not in ['min', 'max', 'equal']:
        raise Exception('operation of filter "' + filter_name + '" is unknown')

    return (filter_key, filter_op)



def queryCars (data_paths_list, filters={}):
    '''Finds objects in specified locations based on specified filters, 
       and returns an index of all suitable objects

       'filters' is a dictionary. E.g. 
          {'pitch.min' : -90, 'pitch.max' : -45, 'name' : 'car'} '''

    # parse filters to operations
    filters_operations = {'min' : {}, 'max' : {}, 'equal' : {}}
    for filter_name, filter_value in filters.iteritems():
        (filter_key, filter_op) = parseFilterName (filter_name)
        filters_operations[filter_op][filter_key] = filter_value
        logging.debug ('filter on ' + filter_op + '(' + str(filter_key) + \
                       ') = ' + str(filter_value))

    response = [];

    # go through directories one by one
    for data_path_template in data_paths_list:
        logging.debug ('query for template: ' + data_path_template)

        # the list probably contains wildcards
        data_paths = glob.glob (data_path_template)
        logging.info ('queryCars found ' + str(len(data_paths)) + \
            ' cars at template path: ' + data_path_template)
        for data_path in data_paths:
            logging.debug ('query for cars in: ' + data_path)

            cars = loadMatCars (data_path)
            take_indices = []
            for i in range(len(cars)):
                car = cars[i]
                carDict = car.toDict()

                will_take = True
                for key, value in filters_operations['min'].iteritems():
                    if key in carDict.keys() and value > carDict[key]:
                        will_take = False
                for key, value in filters_operations['max'].iteritems():
                    if key in carDict.keys() and value < carDict[key]:
                        will_take = False
                for key, value in filters_operations['equal'].iteritems():
                    if key in carDict.keys() and value != carDict[key]:
                        will_take = False

                if will_take:
                    take_indices.append(i)
            
            if take_indices:
                response.append ((data_path, take_indices))

    return response



def clusterCarsIntoGhosts (data_list, filters_path, out_dir):
    '''Cluster cars and save the patches by cluster

       Find cars in paths specified in data_list_path,
       use filters to cluster and transform,
       and save the ghosts '''

    # load clusters
    if not OP.exists(filters_path):
        raise Exception('filters_path does not exist: ' + filters_path)
    filters_file = open(filters_path)
    filters = json.load(filters_file)
    filters_file.close()

    counter_by_cluster = {}

    for filter_ in filters:
        assert ('filter' in filter_)
        cluster_dir = OP.join (out_dir, filter_['filter'])

        # delete 'cluster_dir' dir, and recreate it
        if OP.exists (cluster_dir):
            shutil.rmtree (cluster_dir)
        os.makedirs (cluster_dir)

        counter = 0

        entries = queryCars (data_list, filter_)
        for (cars_path, car_indices) in entries:

            assert OP.exists(cars_path)
            cars = loadMatCars(cars_path)
            cars = [cars[i] for i in car_indices]

            for car in cars:
                filename = "%06d" % counter + IMAGE_EXT
                filepath = OP.join(cluster_dir, filename)
                cv2.imwrite(filepath, car.ghost)
                counter += 1

        counter_by_cluster[filter_['filter']] = counter

    return counter_by_cluster




if __name__ == '__main__':
    ''' Demo '''

    if not os.environ.get('CITY_DATA_PATH') or not os.environ.get('CITY_PATH'):
        print 'First set the environmental variable CITY_PATH, CITY_DATA_PATH'
        sys.exit()
    else:
        CITY_PATH = os.getenv('CITY_PATH')
        CITY_DATA_PATH = os.getenv('CITY_DATA_PATH')

    FORMAT = '%(asctime)s %(levelname)s: \t%(message)s'
    log_path = OP.join (CITY_PATH, 'log/learning/clustering.log')
    logging.basicConfig (format=FORMAT, filename=log_path, level=logging.DEBUG)

    clusters_root = OP.join (CITY_DATA_PATH, 'clustering')

    data_list_path = OP.join (clusters_root, 'data.list')
    if not os.path.exists(data_list_path):
        raise Exception('data_list_path does not exist: ' + data_list_path)
    data_list_file = open(data_list_path, 'r')
    data_list = data_list_file.read().split('\n')
    data_list_file.close()
    # remove empty lines
    data_list = filter(None, data_list)
    # make it relative to the data_list_path
    data_list = [OP.join(CITY_DATA_PATH, x) for x in data_list]

    clusterCarsIntoGhosts (data_list,
                           OP.join (clusters_root, 'by_name/clusters.json'), 
                           OP.join (clusters_root, 'by_name'))
