function downloadSingleCam (camNum, outFileTemplate, numMinutes)
%DOWNLOADSINGLECAM (camNum, outFileTemplate, numMinutes) downloads images 
% from internet and saves them in a video. 
% Separetely write a text file with the time when the frame was created 
% (because it is not 1 sec, but a range 0.6 - 3 sec.)
%
% The filepaths are [outFileTemplate '.avi'] for video
% and [outFileTemplate '.txt'] for text

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

frameReader = FrameReaderInternet (camNum);
frameWriter = FrameWriterVideo (videoPath, 2);
fid = fopen(fullfile(CITY_DATA_PATH, timestampPath), 'w');

t0 = clock;
t = t0;
while etime(t, t0) < numMinutes * 60
    tic
    t = clock;
    [frame, timestamp] = frameReader.getNewFrame();
    frameWriter.step (frame);
    fprintf(fid, '%s\n', timestamp);
    toc
end

fclose(fid);
clear frameReader frameWriter
    
