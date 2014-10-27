function downloadSingleCam (camNum, outDir, numMinutes)
%DOWNLOADSINGLECAM (camNum, outDir, numMinutes) downloads images 
%from internet and saves them in a video. 
%Separetely write a text file with the time when the frame was created 
%(because it is not 1 sec, but a range 0.6 - 3 sec.)
%

clear frameWriter frameReader

% setup data directory
if ~exist('FrameWriter', 'class')
    error ('please "run ../../subdirPathsSetup.m" before calling this function');
end

% where to write video and intervals
videoPath = fullfile(outDir, ['camera' num2str(camNum) '.avi']);
intervalsPath = fullfile(outDir, ['intervals' num2str(camNum) '.txt']);

frameReader = FrameReaderInternet (camNum);
frameWriter = FrameWriterVideo (videoPath, 2, 1);
fid = fopen(intervalsPath, 'w');

t0 = clock;
t = clock;
while etime(t, t0) < numMinutes * 60
    tic
    frame = frameReader.getNewFrame();
    frameWriter.writeNextFrame (frame);
    t = clock;
    fprintf(fid, '%f %f %f %f %f %f \n', t(1), t(2), t(3), t(4), t(5), t(6));
    toc
end

fclose(fid);
clear frameReader frameWriter
    
