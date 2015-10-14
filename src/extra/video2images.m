function video2images (videoPath, outDir)
%DOWNLOADSINGLECAM (camNum, outDir, numFrames) downloads images 
%from internet and saves them in a video. 
%Separetely a text file with time interval between frames is created 
%(because it is not 1 sec, but a range 0.6 - 3 sec.)
%

clear frameWriter frameReader

% setup paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



frameReader = FrameReaderVideo (videoPath);
frameWriter = FrameWriterImages (outDir);

while true
    frame = frameReader.getNewFrame();
    if isempty(frame), break, end
    frameWriter.step (frame);
end

clear frameReader frameWriter
