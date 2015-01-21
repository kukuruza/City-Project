% Write SINGLE frames for Amazon Mech Turk
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


% input
videoDir = [CITY_DATA_PATH, 'camdata/cam572/5pm/'];
frameReader = FrameReaderVideo ([videoDir '15-mins.avi'], [videoDir '15-mins.txt']);

numFramesSkip = 100;
numFramesWrite = 100;
intervalFrames = 5;


% output
outDir = [videoDir 'amazon/frames/'];
frameWriter = FrameWriterImages (outDir, 1, '.jpg');

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


