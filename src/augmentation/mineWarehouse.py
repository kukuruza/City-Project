#!/usr/bin/env python
from contextlib import closing
from selenium.webdriver import Firefox # pip install selenium
from selenium.webdriver.support.ui import WebDriverWait

import urllib2
import logging
import sys, os, os.path as op
import json
import string
import argparse
import shutil

sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from helperSetup import atcity, setupLogging


timeout = 30


# delete special characters
def validateString (str):
    return str.translate(string.maketrans('', ''), '\n\t"\\')


def _find_carmodel_in_vehicles_ (models_info, model_id):
    # TODO: replace sequential search with an elasticsearch index
    for carmodel in models_info:
        if carmodel['model_id'] == model_id:
            return carmodel
    return None



def download_model (browser, url, model_dir, args):

    # model_id is the last part of the url
    model_id = url.split('=')[-1]
    logging.info ('started with model_id: %s' % model_id)

    # open the page with model
    browser.get(url)
    WebDriverWait(browser, timeout=timeout).until(
        lambda x: x.find_element_by_id('title'))

    # get the model name
    model_name = browser.find_element_by_id('title').text.encode("utf-8")
    # delete special characters
    model_name = validateString(model_name)

    # get model description
    description = browser.find_element_by_id('description').text.encode("utf-8")
    # delete special characters
    description = validateString(description)

    model_info = {'model_id':     model_id,
                  'model_name':   model_name,
                  'vehicle_type': args.vehicle_type,
                  'description':  description}
    logging.debug ('vehicle info: %s' % str(model_info))
    print (json.dumps(model_info, indent=4))

    # click on download button
    button = browser.find_element_by_id('button-download')
    button.click()

    # wait for the page to load
    WebDriverWait(browser, timeout=timeout).until(
        lambda x: x.find_element_by_id('download-option-s15'))

    # get the model link
    element = browser.find_element_by_id('download-option-s15')
    skp_href = element.get_attribute('href')

    # download the model
    logging.info ('downloading model_id: %s' % model_id)
    logging.debug('downloading skp from url: %s' % skp_href)
    f = urllib2.urlopen(skp_href)
    skp_path = op.join(model_dir, '%s.skp' % model_id)
    with open(skp_path, 'wb') as local_file:
        local_file.write(f.read())

    # store it to string variable
    #page_source = browser.page_source.encode("utf-8")

    logging.info ('finished with model_id: %s' % model_id)
    return model_info


def download_collection (browser, url, CAD_dir, args):

    # collection_id is the last part of the url
    collection_id = url.split('=')[-1]
    collection_dir = op.join(CAD_dir, collection_id)

    # if collection exists
    models_info = []
    if op.exists(collection_dir):
        # if 'overwrite' enabled, remove everything and write from scratch
        if args.overwrite_collection:
            shutil.rmtree(collection_dir)
        else:
            # if 'overwrite' disabled, try to read what was downloaded
            try:
                collection_path = op.join(collection_dir, 'readme.json')
                collection_info = json.load(open(collection_path))
                models_info = collection_info['vehicles']
            # if 'overwrite' disabled and can't read/parse the readme
            except:
                raise Exception('Failed to continue with collection due to error: %s'
                    % sys.exc_info()[0])
    else:
        os.makedirs(op.join(collection_dir, 'skp'))

    # open the page with model
    browser.get(url)
    WebDriverWait(browser, timeout=timeout).until(
        lambda x: x.find_elements_by_class_name('results-entity-link'))

    # get collection name
    element = browser.find_element_by_id('title')
    collection_name = element.text.encode('utf-8')
    collection_name = validateString(collection_name)

    # get author
    element = browser.find_element_by_id('collection-author')
    author_href = element.get_attribute('href')
    author_id = author_href.split('=')[-1]
    author_name = element.text.encode('utf-8')
    author_name = validateString(author_name)

    # get the model urls
    elements = browser.find_elements_by_class_name('results-entity-link')
    logging.info ('found %d models' % len(elements))
    model_urls = []
    for element in elements:
        model_url = element.get_attribute('href')
        model_urls.append(model_url)

    # bookkeeping
    new_models_info = []
    count_skipped = 0
    count_downloaded = 0
    count_failed = 0

    # got to each model and download it
    for model_url in model_urls:
        model_id = model_url.split('=')[-1]

        # maybe it's already there. Then skip
        model_info = _find_carmodel_in_vehicles_ (models_info, model_id)
        if model_info is not None and ('valid' not in model_info or model_info['valid']):
            logging.info ('skipping previously downloaded model_id %s' % model_id)
            new_models_info.append(model_info)
            count_skipped += 1
            continue

        try:
            logging.debug('model url: %s' % model_url)
            model_dir = op.join(collection_dir, 'skp')
            model_info = download_model (browser, model_url, model_dir, args)
            count_downloaded += 1
        except:
            logging.error('model_id %s was not downloaded because of error: %s'
                % (model_id, sys.exc_info()[0]))
            model_info = {'model_id': model_id, 
                          'valid': False,
                          'comment': 'reason for invalid: timeout error'}
            count_failed += 1
        new_models_info.append(model_info)


    collection_info = {'collection_id': collection_id,
                       'collection_name': collection_name,
                       'author_id': author_id,
                       'author_name': author_name,
                       'vehicles': new_models_info
                       }

    logging.info ('out of %d models in collection: \n' % len(model_urls) +
                  '    skipped:     %d\n' % count_skipped + 
                  '    downloaded:  %d\n' % count_downloaded +
                  '    failed:      %d\n' % count_failed)
    
    with open (op.join(collection_dir, 'readme.json'), 'w') as f:
        f.write(json.dumps(collection_info, indent=4))



if __name__ == "__main__":
    setupLogging('log/augmentation/mineWarehouse.log', logging.INFO, 'w')

    CAD_dir = '/Users/evg/projects/City-Project/data/augmentation/CAD'
    collection_dir = '/Users/evg/projects/City-Project/data/augmentation/CAD/uecadcbca-a400-428d-9240-a331ac5014f6/skp/'
    #url = 'https://3dwarehouse.sketchup.com/model.html?id=4785f0eb63695789ebd80ce91f51b88c'
    url = 'https://3dwarehouse.sketchup.com/collection.html?id=uecadcbca-a400-428d-9240-a331ac5014f6'

    parser = argparse.ArgumentParser()
    parser.add_argument('--overwrite_collection', action='store_true')
    parser.add_argument('--vehicle_type', nargs='?', default='')
    args = parser.parse_args(['--vehicle_type', 'schoolbus'])

    # use firefox to get page with javascript generated content
    with closing(Firefox()) as browser:
        download_collection (browser, url, CAD_dir, args)
        # print download_model (browser, url, collection_dir, args)
