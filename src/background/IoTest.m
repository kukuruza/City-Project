clear all

assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

detector = vision.ForegroundDetector();
image = imread ('testdata/ioTest-fr0.png');
step(detector, image);

image = imread ('testdata/ioTest-fr1.png');
step(detector, image);

feature('SystemObjectsFullSaveLoad',1);
save([CITY_DATA_PATH 'testdata/background/ioTest-detector.mat'], 'detector');

clear all
run '../rootPathsSetup.m';
load([CITY_DATA_PATH 'testdata/background/ioTest-detector.mat']);

anotherDetector = clone(detector);
anotherDetector.isLocked()

%image = imread ('testdata/ioTest-fr0.png');
bimage = imread('../geometry/cam572.png');
%mask = step(detector, image);
