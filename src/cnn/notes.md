HOW TO RUN:

1. `cd City-Project`

2. Training:
    `$CAFFE_ROOT/build/tools/caffe train -solver data/cnn/solvers/sedan-h5.prototxt --logtostderr=0 --log_dir=log/cnn/`

    _NOTE:_ ~~The batch size is kept as 1 in the prototxt file. The number of test examples are mentioned in the solver ( test_iter==number of test examples)~~ HDF5 files are prepared to have a multiple of 100 number of patches.

    _NOTE:_ ~~The train and test files are names train-rgb-b.txt and test-rgb-b.txt respectively inside the prototxt file.~~ Listings of train and test files are now in `data/cnn/lists`.

3. Extracting Features:
	`build/cnn/extract_features_text data/cnn/city/final/city_quick_iter_4000.caffemodel data/cnn/city/final/city_quick_train_test_filters.prototxt conv1 data/cnn/city/features 1 lmdb`

4. Visualization
	`ipython notebook src/cnn/visualization.ipynb`

    _NOTE:_ It uses deploy_python.prototxt

5. C++ Deployment
	`GLOG_minloglevel=2 build/cnn/predict --net data/cnn/architectures/sedan-h5-deploy-cpp.prototxt --model data/cnn/models/sedan-h5_iter_4000.caffemodel --output predicted-cpp.txt`

    _NOTE:_ It uses deploy_cpp.prototxt. The test examples are listed in the file data/cnn/city-data/test-rgb-b.txt. You need to mention this file in the deploy_cpp.prototxt along with number of batches == number of test examples

6. Python Deployment
	`python src/cnn/DeploymentPatches.py`

_NOTE:_ Network prototxt files are in data/cnn/architectures.

_NOTE:_ Test and train text files are in data/cnn/lists.

_NOTE:_ `GLOG_minloglevel=2` before calling a command in terminal suppresses verbose output.

HOW TO CREATE TRAIN AND TEST FILES FOR TRAINING:
1. Split the data into test and train
```
ls -d -1 $PWD/*.*>files.txt
awk '{print $0 " 0"}' files.txt > test-rgb-b.txt
```
