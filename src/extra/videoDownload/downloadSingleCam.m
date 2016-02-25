function counter = downloadSingleCam (camId, outDir, numMinutes, varargin)
%DOWNLOADSINGLECAM (camNum, outFileTemplate, numMinutes) downloads images 
% from internet and saves them in a video. 
% Separetely write a text file with the time when the frame was created 
% (because it is not 1 sec, but a range 0.6 - 3 sec.)
%
% The filepaths are fullfile(outDir 'src.avi') for video
% and fullfile(outDir 'time.txt') for text

parser = inputParser;
addRequired (parser, 'camId', @isscalar);
addRequired (parser, 'outFileTemplate', @ischar);
addRequired (parser, 'numMinutes', @isscalar);
addParameter(parser, 'timeZone', 'America/New_York', @ischar);
addParameter(parser, 'deleteOnExit', false, @islogical);  % use for debugging
parse (parser, camId, outDir, numMinutes, varargin{:});
parsed = parser.Results;

clear frameWriter frameReader

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% make the video dir
if ~exist([CITY_DATA_PATH outDir], 'dir')
    mkdir ([CITY_DATA_PATH outDir]);
end

% where to write video and intervals
videoPath = fullfile(outDir, 'src.avi');
timestampPath = fullfile(outDir, 'time.txt');

% add status updates to remote monitor
monitor = MonitorDownloadClient('config_path', 'etc/monitor.ini', 'cam_id', camId, 'verbose', 1);

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
    monitor.updateDownload(timestamp);
end

fclose(fid);
clear frameReader frameWriter

% during debugging, the script may be run just to check it works.
%   In that case, delete the saved files (return to where we started).
if parsed.deleteOnExit
    rmdir ([CITY_DATA_PATH outDir], 's');
end

    
