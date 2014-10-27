function video2images (videoPath, outDir)
%DOWNLOADSINGLECAM (camNum, outDir, numFrames) downloads images 
%from internet and saves them in a video. 
%Separetely a text file with time interval between frames is created 
%(because it is not 1 sec, but a range 0.6 - 3 sec.)
%

clear frameWriter frameReader

% setup data directory
if ~exist('FrameReader', 'class')
    error ('please run ../subdirPathsSetup.m prior to calling this function');
end



frameReader = FrameReaderVideo (videoPath);
frameWriter = FrameWriterImages (outDir, [1], '.jpg');

while true
    frame = frameReader.getNewFrame();
    if isempty(frame), break, end
    frameWriter.writeNextFrame (frame);
end

clear frameReader frameWriter
