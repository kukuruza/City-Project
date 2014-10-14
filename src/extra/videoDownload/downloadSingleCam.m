function downloadSingleCam (camNum, outDir, numFrames)
%DOWNLOADSINGLECAM (camNum, outDir, numFrames) downloads images 
%from internet and saves them in a video. 
%Separetely a text file with time interval between frames is created 
%(because it is not 1 sec, but a range 0.6 - 3 sec.)
%

clear frameWriter frameReader

% setup data directory
if ~exist('FrameWriter', 'class')
    error ('please run ../../subdirPathsSetup.m prior to calling this function');
end

% where to write video and intervals
videoPath = fullfile(outDir, ['camera' num2str(camNum) '.avi']);
intervalsPath = fullfile(outDir, ['intervals' num2str(camNum) '.txt']);

frameReader = FrameReaderInternet (camNum);
frameWriter = FrameWriterVideo (videoPath, 2, 1);
fid = fopen(intervalsPath, 'w');

for t = 1 : numFrames
    tic
    [frame, interval] = frameReader.getNewFrame();
    frameWriter.writeNextFrame (frame);
    fprintf(fid, '%f\n', interval);
    toc
end

fclose(fid);
clear frameReader frameWriter
    
