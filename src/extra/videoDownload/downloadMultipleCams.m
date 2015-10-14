function downloadMultipleCams (camListPath, numMinutes, varargin)
% Download video from a bunch of cameras.
% This functon knows about our organization of data, e.g.
%   camdata/cam001/Jan01-01h
%
% Input:
%   camListPath - path (relative to 'relpath') to text file with list of cameras
%   numMinutes  - number of minutes to download video for
% Optional parameters:
%   relpath     - defaults to CITY_DATA_PATH
%   timeZone    - one of IANA timezones, defaults to NYC


% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input

parser = inputParser;
addRequired(parser, 'camListPath', @ischar);
addRequired(parser, 'numMinutes', @isscalar);
addParameter(parser, 'relpath', CITY_DATA_PATH, @ischar);
addParameter(parser, 'timeZone', 'America/New_York', @ischar);
parse (parser, camListPath, numMinutes, varargin{:});
parsed = parser.Results;


%% work

% read camIds from file
assert (exist(fullfile(parsed.relpath, camListPath), 'file') ~= 0);
lineList = readList(fullfile(parsed.relpath, camListPath));
camIds = zeros(length(lineList), 1);
for i = 1 : length(lineList)
    camIds(i) = sscanf(lineList{i}, '%d');
end

% get the video name, same for each cam. (maybe move into downloadSingleCam)
name = [datestr(datetime('now','TimeZone', parsed.timeZone), 'mmmdd-HH'), 'h'];

% start downloading each camera
taskPool = gcp();
fprintf ('Have %d workers.\n', taskPool.NumWorkers);
for i = 1 : length(camIds)
    
    camId = camIds(i);
    camDir = fullfile('camdata', sprintf('cam%03d', camId));
    outFileTemplate = fullfile(camDir, name);
    fprintf ('Downloading from camera template: %s \n', outFileTemplate);
    
    % create the camera directory, if it doesn't exist
    if ~exist (fullfile(getenv('CITY_DATA_PATH'), camDir), 'dir')
        mkdir (fullfile(getenv('CITY_DATA_PATH'), camDir));
    end
    
    f(i) = parfeval (taskPool, @downloadSingleCam, 1, camId, outFileTemplate, numMinutes, 'timeZone', parsed.timeZone);
end

% wait for each worker
for i = 1 : length(camIds)
  [completedIdx, numFrames] = fetchNext(f);
  fprintf('Camera %d wrote %d frames (task %d).\n', camIds(i), numFrames, completedIdx);
end
fprintf ('Finished download from all cameras.\n');

delete(gcp('nocreate'))
