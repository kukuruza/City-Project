# activate virtualenv
source $HOME/src/tensorflow/virtualenv1/bin/activate

# the first argument specifies the log directory
LOG_DIR=$1

# start tensorflow server in background
python $HOME/src/tensorflow/virtualenv1/lib/python2.7/site-packages/tensorflow/tensorboard/backend/tensorboard.py --logdir $LOG_DIR >> $CITY_PATH/log/tensorflow/tensorboard.log 2>&1
