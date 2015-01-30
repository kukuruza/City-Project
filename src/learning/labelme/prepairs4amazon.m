% Write pairs of frames for Amazon Mech Turk
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

% output
outDir = [videoDir 'amazon/pairs/'];
frameWriter = FrameWriterImpairs (outDir);

for i = 1 : 100
    frame = frameReader.getNewFrame();
    if isempty(frame), break, end
    
    frameWriter.writeNextFrame(frame, sprintf('%03d', i));
end

clear frameReader frameWriter


