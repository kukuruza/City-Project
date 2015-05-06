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
videoPath = fullfile([CITY_DATA_PATH outFileTemplate, '.avi']);
intervalsPath = fullfile([CITY_DATA_PATH outFileTemplate,'.txt']);
sampleImagePath = fullfile([CITY_DATA_PATH outFileTemplate,'.jpg']);

fprintf ('Will write video to %s\n', videoPath);
fprintf ('Will write time  to %s\n', intervalsPath);

frameReader = FrameReaderInternet (camNum);
frameWriter = FrameWriterVideo (videoPath, 2, 1);
fid = fopen(intervalsPath, 'w');

t0 = clock;
t = t0;
while etime(t, t0) < numMinutes * 60
    tic
    frame = frameReader.getNewFrame();
    frameWriter.writeNextFrame (frame);
    if t == t0, imwrite (frame, sampleImagePath); end
    t = clock;
    fprintf(fid, '%f %f %f %f %f %f \n', t(1), t(2), t(3), t(4), t(5), t(6));
    toc
end

fclose(fid);
clear frameReader frameWriter
    
