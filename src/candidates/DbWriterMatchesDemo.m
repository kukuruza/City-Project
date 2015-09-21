% Save the matches into a database using the database writer
% Demo for DataabaseWriter for all the features

clear all;

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

%% input

% What to do
write = true;
show = true;

% Setting up the paths for input and reference database
dbPath = fullfile(CITY_DATA_PATH, 'matches', 'matches-demo.db');
refPath = fullfile(CITY_DATA_PATH, 'datasets/labelme/Databases/572-Oct30-17h-pair/init-ghost.db');
videoPathRel = fullfile('springfield', 'may16/cam48.avi');
videoPathAbs = fullfile(CITY_DATA_PATH, videoPathRel);

%% Work

% Creating a simple DatabaseWriter instance
if write
    writer = DatabaseWriter(dbPath, refPath);
end

noFrames = 100;
for i = 1:noFrames
    %----------------------------------------------------------------------
    % We randomly dump matches to check for working of functionality of
    % DatabaseWriter
    % These values are to be obtained from tracker
    
    % Random number of tracklets for this frame
    noCars = randi([0 3], 1);
    % Randomly select number of matches for each car
    noMatches = randi([2 6], noCars, 1);
    % Save each match one-by-one
    for j = 1:noCars
        % Random bounding boxes for each car, each match
        bboxes = randi([1, 200], noMatches(j), 4);
        frameId = randi([1 100], noMatches(j), 1);
        
        writer.saveMatchesToDatabase(videoPathRel, frameId, bboxes);
    end
    %----------------------------------------------------------------------
end

% Closing the database / DatabaseWriter
if write
    writer.closeDatabase();
end