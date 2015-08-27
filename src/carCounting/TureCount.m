%
% example of reading all matching cars from dababase to matlab
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input
% db_path = fullfile(CITY_DATA_PATH, 'datasets/labelme/Databases/572-Oct30-17h-pair/parsed.db');
GT_db_path = [CITY_DATA_PATH, 'datasets/labelme/Databases/572-Nov28-10h-pair/parsed.db'];



%% show all information about every match in every image

% open database
sqlite3.open (GT_db_path);

AllMatch = sqlite3.execute('SELECT match FROM matches');
% read imagefiles, each of them is a pair of images
imagefiles = sqlite3.execute('SELECT imagefile FROM images');
b = zeros(100, 1);
for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    car_entries = sqlite3.execute('SELECT * FROM cars WHERE imagefile = ?', imagefile);
     b(i) = length(car_entries);
end
save('TrueCount.mat','b');
sqlite3.close();


