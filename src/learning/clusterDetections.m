% Cluster detected cars based on orientation and size

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


%% input

inPatchesDir = [CITY_DATA_PATH 'testdata/learned/patches/'];
inCarsDir = [CITY_DATA_PATH 'testdata/learned/cars/'];


%% work with all cars

carsList = dir([inCarsDir '*-car*.mat']);

sizes = zeros(length(carsList), 1);
orientations = zeros(length(carsList), 2);  % N x [yaw, pitch]

for i = 1 : length(carsList)
    % load car object
    clear car
    load ([inCarsDir carsList(i).name]);
    
    sizes(i) = (car.bbox(3) + car.bbox(4)) / 2;
    orientations(i,:) = car.orientation;
end
