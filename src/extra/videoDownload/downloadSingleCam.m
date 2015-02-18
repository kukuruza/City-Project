function downloadSingleCam (camNum, outFileTemplate, numMinutes)
%DOWNLOADSINGLECAM (camNum, outFileTemplate, numMinutes) downloads images 
% from internet and saves them in a video. 
% Separetely write a text file with the time when the frame was created 
% (because it is not 1 sec, but a range 0.6 - 3 sec.)
%
% The filepaths are [outFileTemplate '.avi'] for video
% and [outFileTemplate '.txt'] for text

clear frameWriter frameReader

% setup data directory
if ~exist('FrameWriter', 'class')
    error ('please "run ../../subdirPathsSetup.m" before calling this function');
end

% where to write video and intervals
videoPath = fullfile([outFileTemplate, '.avi']);
intervalsPath = fullfile([outFileTemplate,'.txt']);

fprintf ('Will write video to %s\n', videoPath);
fprintf ('Will write subtitles to %s\n', intervalsPath);

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
    
