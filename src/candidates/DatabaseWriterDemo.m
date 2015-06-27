% Save the candidates into a database using the database writer
% Demo for DataabaseWriter for all the features

clear all;

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% Setting up the paths for input and reference database
dbPath = 'databaseWriterDemo.db';
refPath = fullfile(CITY_DATA_PATH, 'datasets/sparse/Databases/671-Mar24-12h',...
                    'src.db');

% Creating a simple DatabaseWriter instance
writer = DatabaseWriter(dbPath, refPath);             

% writing a test bbox for functionality verification
% writer.saveBoxesToDatabase([1 2 3 4], 'someImage.png');

% CameraId
sizeMapPath = fullfile(CITY_DATA_PATH, 'models/cam671/', 'mapSize.tiff');
imageDir = fullfile(CITY_DATA_PATH, 'datasets/sparse/Images/671-Mar24-12h/');

% Size map
mapSize = imread(sizeMapPath);
% Reading the images in a loop
imgListing = dir([imageDir, '*.jpg']);

for i = 1:2%length(imgListing)
    image = imread(imgListing(i).name);
    
    % Size map based candidates
    %cands = CandidatesSizemap (mapSize);
    
    % Selective Search wrapper
    cands = CandidatesSelectSearch('mapSize', mapSize);
    
    % Getting the candidates
    %bboxes = cands.getCandidates();
    bboxes = cands.getCandidates('image', image);
    
    % Writing the candidates
    writer.saveBoxesToDatabase(bboxes, imgListing(i).name);
end

% Closing the database / DatabaseWriter
writer.closeDatabase();