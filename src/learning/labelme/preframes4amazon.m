% Write SINGLE frames for Amazon Mech Turk
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;


% input
videoDir = [CITY_DATA_PATH, 'camdata/cam578/'];
frameReader = FrameReaderVideo ([videoDir 'Jan22-14h-sunny.avi'], [videoDir 'Jan22-14h-sunny.txt']);

numFramesSkip = 0;
numFramesWrite = 200;
intervalFrames = 1;


% output
outDir = [CITY_DATA_PATH 'labelme/Images/cam578-Jan22-14h/'];
frameWriter = FrameWriterImages (outDir, [1 1], '.jpg');

% skip first N frames
for i = 1 : numFramesSkip
    frame = frameReader.getNewFrame();
end

% write frames
for i = 1 : numFramesWrite
    frame = frameReader.getNewFrame();
    if isempty(frame), break, end
    
    frameWriter.writeNextFrame(frame);
    
    for j = 1 : intervalFrames-1
        frame = frameReader.getNewFrame();
        if isempty(frame), break, end
    end
end

clear frameReader frameWriter


