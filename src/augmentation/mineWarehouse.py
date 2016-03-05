#!/usr/bin/env python
from contextlib import closing
from selenium.webdriver import Firefox # pip install selenium
from selenium.webdriver.support.ui import WebDriverWait

import sys, os, os.path as op
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src'))
import urllib2
import logging
import json
import string
import argparse
import shutil
import time
import traceback

from learning.helperSetup import atcity, setupLogging
from Cad import Cad



CAD_DIR = atcity('augmentation/CAD')
README_NAME = 'readme-src.json'


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
    WebDriverWait(browser, timeout=args.timeout).until(
        lambda x: x.find_element_by_id('title'))

    # get the model name
    element = browser.find_element_by_id('title')
    model_name = validateString(element.text.encode('ascii','ignore'))

    # get model description
    element = browser.find_element_by_id('description')
    description = validateString(element.text.encode('ascii','ignore'))

    model_info = {'model_id':     model_id,
                  'model_name':   model_name,
                  'vehicle_type': args.vehicle_type,
                  'description':  description,
                  'valid':        True}
    logging.debug ('vehicle info: %s' % str(model_info))
    print (json.dumps(model_info, indent=4))

    skp_path = op.join(model_dir, '%s.skp' % model_id)
    if op.exists(skp_path): 
        logging.info ('skp file already exists for model_id: %s' % model_id)
        return model_info

    # click on download button
    button = browser.find_element_by_id('button-download')
    button.click()

    # wait for the page to load the download buttons
    #   we check the latest skp versin first, then next, and next. Then raise.
    for skp_version in ['s15', 's14', 's13', None]:
        # skp_version None is the marker to give up
        if skp_version is None:
            raise Exception('Cannot find skp versions 15, 14, or 13')
        try:
            logging.info('trying to download skp version %s' % skp_version)
            WebDriverWait(browser, timeout=args.timeout).until(
                lambda x: x.find_element_by_id('download-option-%s' % skp_version))
            break
        except:
            logging.info('model has not skp version %s. Try next.' % skp_version)


    # get the model link
    element = browser.find_element_by_id('download-option-%s' % skp_version)
    skp_href = element.get_attribute('href')

    # download the model
    logging.info ('downloading model_id: %s' % model_id)
    logging.debug('downloading skp from url: %s' % skp_href)
    f = urllib2.urlopen(skp_href)
    with open(skp_path, 'wb') as local_file:
        local_file.write(f.read())

    logging.info ('finished with model_id: %s' % model_id)
    return model_info



def download_all_models (model_urls, models_info, collection_id, collection_dir):

    new_models_info = []
    counts = {'skipped': 0, 'downloaded': 0, 'failed': 0}

    # got to each model and download it
    for model_url in model_urls:
        model_id = model_url.split('=')[-1]
        model_info = _find_carmodel_in_vehicles_ (models_info, model_id)

        # if this model was previously failed to be recorded
        if model_info is not None:
            if 'valid' in model_info and not model_info['valid']:
                assert 'error' in model_info
                if model_info['error'] == 'download failed: timeout error':
                    logging.info ('re-doing previously failed download: %s' % model_id)
                else:
                    logging.info ('skipping bad for some reason model: %s' % model_id)
                    counts['skipped'] += 1
                    continue
            else:
                logging.info ('skipping previously downloaded model_id %s' % model_id)
                model_info['valid'] = True
                counts['skipped'] += 1
                continue

        # check if this model is known as a part of some other collection
        seen_collection_ids = cad.is_model_in_other_collections (model_id, collection_id)
        if seen_collection_ids:
            error = 'is a part of %d collections. First is %s' % \
                         (len(seen_collection_ids), seen_collection_ids[0])
            model_info['valid'] = False
            model_info['error'] = error
            logging.warning ('model_id %s %s' % (model_id, error))
            counts['skipped'] += 1
            cad.update_model (model_info, collection_id)
            new_models_info.append(model_info)
            continue

        # process the model
        try:
            logging.debug('model url: %s' % model_url)
            model_dir = op.join(collection_dir, 'skp_src')
            model_info = download_model (browser, model_url, model_dir, args)
            counts['downloaded'] += 1
        except:
            logging.error('model_id %s was not downloaded because of error: %s'
               % (model_id, traceback.format_exc()))
            model_info = {'model_id': model_id, 
                          'valid': False,
                          'error': 'download failed: timeout error'}
            counts['failed'] += 1

        cad.update_model (model_info, collection_id)
        new_models_info.append(model_info)

    logging.info ('out of %d models in collection: \n' % len(model_urls) +
                  '    skipped:     %d\n' % counts['skipped'] + 
                  '    downloaded:  %d\n' % counts['downloaded'] +
                  '    failed:      %d\n' % counts['failed'])

    return new_models_info    



def download_collection (browser, collection_id, cad, args):

    # collection_id is the last part of the url
    url = 'https://3dwarehouse.sketchup.com/collection.html?id=' + collection_id
    collection_dir = op.join(CAD_DIR, collection_id)
    logging.info ('will download coleection_id: %s' % collection_id)

    # if collection exists
    collection_path = op.join(collection_dir, README_NAME)
    if op.exists(collection_path):
        # if 'overwrite' enabled, remove everything and write from scratch
        if args.overwrite_collection:
            shutil.rmtree(collection_dir)
        else:
            # if 'overwrite' disabled, try to read what was downloaded
            try:
                collection_info = json.load(open(collection_path))
                models_info = collection_info['vehicles']
            # if 'overwrite' disabled and can't read/parse the readme
            except:
                raise Exception('Failed to parse the collection due to: %s'
                    % sys.exc_info()[0])
    else:
        models_info = []
        if not op.exists(op.join(collection_dir, 'skp_src')):
            os.makedirs(op.join(collection_dir, 'skp_src'))

    # open the page with collection
    browser.get(url)
    WebDriverWait(browser, timeout=args.timeout).until(
        lambda x: x.find_elements_by_class_name('results-entity-link'))

    # get collection name
    element = browser.find_element_by_id('title')
    collection_name = validateString(element.text.encode('ascii', 'ignore'))

    # get collection description
    element = browser.find_element_by_id('description')
    collection_description = validateString(element.text.encode('ascii','ignore'))

    # get collection tags
    #element = browser.find_element_by_id('tags')
    #element.find_element_by_xpath(".//p[@id='test']").text 
    #collection_name = element.text.encode('ascii','ignore')
    #collection_name = validateString(collection_name)

    # get author
    element = browser.find_element_by_id('collection-author')
    author_href = element.get_attribute('href')
    author_id = author_href.split('=')[-1]
    author_name = validateString(element.text.encode('ascii','ignore'))

    # keep scrolling the page until models show up (for pages with many models)
    prev_number = 0
    while True:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        elements = browser.find_elements_by_class_name('results-entity-link')
        logging.info ('found %d models' % len(elements))
        if prev_number == len(elements):
            break
        else:
            prev_number = len(elements)
            time.sleep(1)
    # get the model urls
    model_urls = []
    for element in elements:
        model_url = element.get_attribute('href')
        model_urls.append(model_url)

    # download all models
    new_models_info = download_all_models (model_urls, models_info, 
                                           collection_id, collection_dir)

    collection_info = {'collection_id': collection_id,
                       'collection_name': collection_name,
                       'author_id': author_id,
                       'author_name': author_name,
                       'vehicles': new_models_info
                       }

    with open (op.join(collection_dir, README_NAME), 'w') as f:
        f.write(json.dumps(collection_info, indent=4))




if __name__ == "__main__":
    setupLogging('log/augmentation/MineWarehouse.log', logging.INFO, 'w')

    parser = argparse.ArgumentParser()
    parser.add_argument('--collection_id')
    parser.add_argument('--overwrite_collection', action='store_true')
    parser.add_argument('--vehicle_type', nargs='?', default='object')
    parser.add_argument('--timeout', nargs='?', default=10, type=int)
    args = parser.parse_args()

    cad = Cad()

    # use firefox to get page with javascript generated content
    with closing(Firefox()) as browser:
        download_collection (browser, args.collection_id, cad, args)
