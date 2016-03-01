function makeMultipleMaskBack (camListFile, videoName, varargin)
% Download video from a bunch of cameras.
% This functon knows about our organization of data, e.g.
%   camdata/cam001/Jan01-01h
%
% Input:
%   camListPath - path (relative to 'relpath') to text file with list of cameras,
%                   this file must have one camera number per line
%   numMinutes  - number of minutes to download video for
% Optional parameters:
%   relpath     - defaults to CITY_DATA_PATH
%   timeZone    - the default '-05:00' (for NYC in winter time)


% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input

parser = inputParser;
addRequired(parser, 'camListPath', @ischar);
addRequired(parser, 'videoName', @ischar);
addParameter(parser, 'relpath', CITY_DATA_PATH, @ischar);
addParameter(parser, 'verbose', 1, @isscalar);
parse (parser, camListFile, videoName, varargin{:});
parsed = parser.Results;

if parsed.verbose
    fprintf ('CITY_DATA_PATH:        %s.\n', CITY_DATA_PATH);
    fprintf ('videoName:             %s.\n', parsed.videoName);
    fprintf ('relPath:               %s.\n', parsed.relpath);
    fprintf ('camListPath full path: %s.\n', fullfile(parsed.relpath, camListFile));
end

%% work

% read camIds from file
assert (exist(fullfile(parsed.relpath, camListFile), 'file') ~= 0);
lineList = readList(fullfile(parsed.relpath, camListFile));
camIds = zeros(length(lineList), 1);
for i = 1 : length(lineList)
    try
        camIds(i) = sscanf(lineList{i}, '%d');
    catch
        warning('cant read line %d of the list', i);
    end
end

% process each file
for i = 1 : length(lineList)
    in_video_dir = sprintf ('camdata/cam%d/%s', camIds(i), videoName);
    fprintf ('processing video dir %s\n', in_video_dir);
    try
        MakeMaskVideo (in_video_dir);
        MakeBackVideo (in_video_dir);
    catch
        fprintf ('Error with video_dir %s. Move on.\n', in_video_dir);
    end
end
