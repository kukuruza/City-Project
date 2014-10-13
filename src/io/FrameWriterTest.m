% Test FrameWriter-s
%
% The function reads 30 frames from 2 videos and writes the result
%

clear all

% setup data directory
run '../rootPathsSetup.m';

% we will use two frames
frameReader1 = FrameReaderImages ([CITY_DATA_PATH, '2-min/camera360/']);
frameReader2 = FrameReaderImages ([CITY_DATA_PATH, '2-min/camera368/']);

% create the FrameWriter object
outputDir = fullfile(CITY_DATA_PATH, 'testdata', 'FrameWriter');
%frameWriter = FrameWriterVideo (fullfile(outputDir, 'test.avi'), 2);%, [1, 2], [300, 800]);

frameWriter = FrameWriterImpairs (outputDir);

for i = 1 : 10
    frame1 = frameReader1.getNewFrame();
    frame2 = frameReader2.getNewFrame();
    if isempty(frame1), break, end
    
    cellframes{1} = frame1;
    % frameWriter.writeNextFrame(cellframes);
    
    frameWriter.writeNextFrame (frame1, sprintf('%02d', i));
end


