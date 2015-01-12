% Test FrameWriter-s
%
% The function reads 30 frames from 2 videos and writes the result
%

clear all

% setup data directory
run '../rootPathsSetup.m';

% image sources
frameReader1 = FrameReaderImages ([CITY_DATA_PATH, 'camdata/2-min/camera360/']);
frameReader2 = FrameReaderImages ([CITY_DATA_PATH, 'camdata/2-min/camera368/']);


outDir = [CITY_DATA_PATH, 'testdata/io/FrameWriterImages/'];
frameWriter = FrameWriterImages (outDir, [1, 2], '.jpg');

%outPath = [CITY_DATA_PATH, 'testdata/io/FrameWriterVideo/test.avi'];
%frameWriter = FrameWriterVideo (outPath, 2, 1);

%outDir = fullfile(CITY_DATA_PATH, 'testdata', 'FrameWriterImpairs');
%frameWriter = FrameWriterImpairs (outputDir);

for i = 1 : 10
    frame1 = frameReader1.getNewFrame();
    frame2 = frameReader2.getNewFrame();
    if isempty(frame1), break, end
    
    % test FrameWriterImages and FrameWriterVideo
    frameWriter.writeNextFrame({frame1, frame2});
    
    % test FrameWriterImpair
    %frameWriter.writeNextFrame (frame1, sprintf('%02d', i));
end

clear frameWriter


