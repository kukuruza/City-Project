function counter = downloadSingleCam (camId, outFileTemplate, numMinutes, varargin)
%DOWNLOADSINGLECAM (camNum, outFileTemplate, numMinutes) downloads images 
% from internet and saves them in a video. 
% Separetely write a text file with the time when the frame was created 
% (because it is not 1 sec, but a range 0.6 - 3 sec.)
%
% The filepaths are [outFileTemplate '.avi'] for video
% and [outFileTemplate '.txt'] for text

parser = inputParser;
addRequired (parser, 'camId', @isscalar);
addRequired (parser, 'outFileTemplate', @ischar);
addRequired (parser, 'numMinutes', @isscalar);
addParameter(parser, 'timeZone', 'America/New_York', @ischar);
parse (parser, camId, outFileTemplate, numMinutes, varargin{:});
parsed = parser.Results;

clear frameWriter frameReader

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% where to write video and intervals
videoPath = [outFileTemplate, '.avi'];
timestampPath = [outFileTemplate,'.txt'];

fprintf ('Will write video to %s\n', videoPath);
fprintf ('Will write time  to %s\n', timestampPath);

frameReader = FrameReaderInternet (camId, 'timeZone', parsed.timeZone);
frameWriter = FrameWriterVideo (videoPath, 2);
fid = fopen(fullfile(CITY_DATA_PATH, timestampPath), 'w');

counter = 0; % for output
t0 = clock;
t = t0;
while etime(t, t0) < numMinutes * 60
    tic
    t = clock;
    [frame, timestamp] = frameReader.getNewFrame();
    frameWriter.step (frame);
    fprintf(fid, '%s\n', timestamp);
    toc
    counter = counter + 1;
end

fclose(fid);
clear frameReader frameWriter
    
