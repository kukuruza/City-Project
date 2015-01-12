%learnBackgroundGMM runs the background model for many frames and saves
% the learned model to file
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

% input frames
inDir = 'camdata/cam572/10am/';
videoPath = [CITY_DATA_PATH, inDir, '2-hours.avi'];
timesPath = [CITY_DATA_PATH, inDir, '2-hours.txt'];
%frameReader = FrameReaderImages ([CITY_DATA_PATH, inDir]); 
frameReader = FrameReaderVideo (videoPath, timesPath); 

% background
background = BackgroundGMM();

% output model
outputPath = [CITY_DATA_PATH, inDir, 'models/backgroundGMM.mat'];

for t = 1 : 1000
    fprintf ('.');
    if mod(t, 50) == 0, fprintf ('\n'); end
    
    % read image
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    
    % subtract backgroubd and return mask
    mask = background.subtract(frame);

    % show mask
    figure(1)
    subplot(1,2,1), imshow(frame);
    subplot(1,2,2), imshow(mask);
    pause (0.2);
end

% save model
save(outputPath, 'background');

clear frameReader
