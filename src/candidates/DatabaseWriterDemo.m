% Save the candidates into a database using the database writer
% Demo for DataabaseWriter for all the features

%clear all;

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% Setting up the paths for input and reference database
dbPath = fullfile(CITY_DATA_PATH, 'cnn/candidates', '671-Mar24-12h_selective.db');
%dbPath = fullfile(CITY_DATA_PATH, 'cnn/candidates', '671-Mar24-12h_sizemap.db');
refPath = fullfile(CITY_DATA_PATH, 'datasets/sparse/Databases/671-Mar24-12h',...
                    'src-image.db');

% CameraId
sizeMapPath = fullfile(CITY_DATA_PATH, 'models/cam671/', 'mapSize.tiff');
imageSetPath = 'datasets/sparse/Images/671-Mar24-12h';
imageDir = fullfile(CITY_DATA_PATH, imageSetPath);

% Creating a simple DatabaseWriter instance
writer = DatabaseWriter(dbPath, refPath, imageSetPath);

% Size map
mapSize = imread(sizeMapPath);
% Reading the images in a loop
imgListing = dir(fullfile(imageDir, '*.jpg'));

% Getting the boxes before for the camera(only if based on sizemap
% candidates)
%cands = CandidatesSizemap (mapSize);
%imageBboxes = cands.getCandidates();
%bg = BackgroundGMM();

% Selective Search candidates
cands = CandidatesSelectSearch('mapSize', mapSize);
    
for i = 1:length(imgListing)
    image = imread(fullfile(imageDir, imgListing(i).name));
    
    % Size map based candidates
    % Get the candidates filtered by background
    %background = bg.subtract(image);
    %bboxes = cands.filterCandidatesBackground(imageBboxes, background);
    
    % Getting the candidates (selective search)
    bboxes = cands.getCandidates('image', image);
    
    %debugImg = cands.drawCandidates(bboxes, image);
%     bboxes = cands.getCandidates('image', image);
    
    % Writing the candidates
    writer.saveBoxesToDatabase(bboxes, i, size(image));
    
    % Displaying the image
    fprintf('%d / %d\n', i, length(imgListing));
end

% Closing the database / DatabaseWriter
writer.closeDatabase();