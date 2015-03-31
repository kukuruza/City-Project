import logging
import sys
import os, os.path as op
import shutil
import glob
import json
import random
from optparse import OptionParser

sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning'))
from setup_helper import setupLogging, get_CITY_DATA_PATH, setParamUnlessThere
from opencvInterface import loadJson, execCommand, ExperimentsBuilder


def train (experiment, mem):

    CITY_DATA_PATH = get_CITY_DATA_PATH()

    experiment = setParamUnlessThere (experiment, 'num_neg_images', 1000)
    experiment = setParamUnlessThere (experiment, 'frac_pos_use', 0.9)
    experiment = setParamUnlessThere (experiment, 'neg_to_pos_ratio', 3)
    experiment = setParamUnlessThere (experiment, 'num_stages', 20)
    experiment = setParamUnlessThere (experiment, 'feature_type', 'HAAR')
    experiment = setParamUnlessThere (experiment, 'min_hit_rate', 0.995)
    experiment = setParamUnlessThere (experiment, 'max_false_alarm_rate', 0.5)

    model_dir        = experiment['model_dir']
    dat_path         = experiment['dat_path']
    background_files = experiment['background_files']
    w                = experiment['w']
    h                = experiment['h']

    # model dir
    model_dir = op.join(CITY_DATA_PATH, model_dir)
    logging.info ('model_dir: ' + model_dir)
    if op.exists (model_dir):
        logging.warning ('will delete existing model_dir: ' + model_dir)
        shutil.rmtree (model_dir)
    os.makedirs (model_dir)

    # .dat positives
    dat_path = op.join(CITY_DATA_PATH, dat_path)
    if not op.exists (dat_path):
        raise Exception ('dat_path does not exist: ' + dat_path)
    # FIXME: this only works for one bbox per line
    total_num_pos = sum(1 for line in open(dat_path))
    assert (total_num_pos > 0)

    # create .vec positives
    vec_name = op.splitext(op.basename(dat_path))[0] + '.vec'
    vec_path = op.join(op.dirname(dat_path), vec_name)
    logging.info ('vec_path: ' + vec_path)
    if not op.exists(vec_path):
        logging.info ('will create .vec file from .dat file')
        command = ['opencv_createsamples', '-vec', vec_path, '-info', dat_path,
                   '-num', str(total_num_pos), '-w', str(w), '-h', str(h),
                   '-maxxangle', '0', '-maxyangle', '0', '-maxzangle', '0']
        logpath = op.join(model_dir, 'opencv_createsamples.out')
        execCommand (command, logpath, wait=True)

    # dir with negatives
    background_files = op.join(CITY_DATA_PATH, background_files)
    if not glob.glob (background_files):
        raise Exception ('background_files do not exist: ' + background_files)

    # make .info negatives
    neg_list = glob.glob(background_files)
    assert (neg_list)
    logging.info ('found ' + str(len(neg_list)) + ' negative files')
    # keep at most num_neg_images negatives
    num_neg_images = experiment['num_neg_images']
    logging.info ('will keep no more than ' + str(num_neg_images))
    random.shuffle(neg_list)
    if len(neg_list) > num_neg_images:
        neg_list = neg_list[:num_neg_images]
    # write negative paths into .info file
    info_path = op.join(model_dir, 'negatives.info')
    with open(info_path, 'w') as info_file:
        for item in neg_list:
            info_file.write("%s\n" % item)

    # actual number of positives and negatives
    num_pos = int(total_num_pos * experiment['frac_pos_use'])
    num_neg = int(num_pos * experiment['neg_to_pos_ratio'])

    os.chdir (model_dir)
    assert (op.exists(op.basename(info_path)))

    # train
    command = ['opencv_traincascade', '-data', model_dir, '-vec', vec_path,
               '-bg', op.basename(info_path), '-w', str(w), '-h', str(h),
               '-precalcValBufSize', str(mem), '-precalcIdxBufSize', str(mem),
               '-numPos',            str(num_pos), 
               '-numNeg',            str(num_neg),
               '-numStages',         str(experiment['num_stages']),
               '-featureType',       str(experiment['feature_type']),
               '-minHitRate',        str(experiment['min_hit_rate']),
               '-maxFalseAlarmRate', str(experiment['max_false_alarm_rate']) ]
    logpath = op.join(model_dir, 'opencv_traincascade.out')
    execCommand (command, logpath, wait=False)

    readme_path = op.join(model_dir, 'experiment.json')
    with open(readme_path, 'w') as readme_file:
        readme_file.write(json.dumps(experiment, indent=4) + '\n')

    logging.info ('started experiment ' + experiment['model_dir'])



def trainAll(task_path, mem):
    random.seed(0)
    for experiment in ExperimentsBuilder(loadJson(task_path)).getResult():
        train (experiment, mem)
    logging.info ('all experiments successfully started. Quitting.')



if __name__ == '__main__':

    setupLogging ('log/detector/runTrainTask.log', logging.INFO, 'a')

    parser = OptionParser(description='''Start opencv_traincascade
                                    task, described in a json format file''')
    parser.add_option('--task_path', type=str, nargs='?',
                      default='learning/violajones/tasks/test.json',
                      help='path to json file with task description')
    parser.add_option('--mem', type=int,
                      default=1024,
                      help='memory that opencv_traincascade can use')
    parser.add_option('--show_experiments', action='store_true',
                      default=False,
                      help='print out experiment configurations and then quit')
    (options, args) = parser.parse_args()
    logging.info ('argument list: ' + str(options))

    if options.show_experiments:
        experiments = ExperimentsBuilder(loadJson(options.task_path)).getResult()
        print (json.dumps(experiments, indent=4))
        sys.exit()

    trainAll (options.task_path, options.mem)
