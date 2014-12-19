% Cluster detected cars based on orientation and size

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


%% output

outPatchesDir = [CITY_DATA_PATH 'testdata/learned/patches/'];
outCarsDir = [CITY_DATA_PATH 'testdata/learned/cars/'];


%% 
