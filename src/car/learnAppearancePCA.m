% learn PCA of car appearance features
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

% input cars
inCarsDir = [CITY_DATA_PATH 'testdata/detector/detections/'];
carsList = dir([inCarsDir '*car*.mat']);

for i = 1 : length(carsList)

    % load car object
    clear car
    load ([inCarsDir carsList(i).name]);
    
    car.generateFeature();
    
    error ('r')
    %feature = 
    
    % all features in one matrix
%A = zeros()
end

