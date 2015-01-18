% generateBackimage -- makes it up for a missing function in BackgroundGMM
%   It generates a background image from a set of frames,
%   for every pixel the most recent frame that contained background is picked

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


% input
inVideoDir = [CITY_DATA_PATH 'camdata/cam572/5pm/'];
inVideoPath = [inVideoDir '15-mins.avi'];
inTimestampPath = [inVideoDir '15-mins.txt'];
% inVideoDir = [CITY_DATA_PATH 'camdata/cam572/10am/'];
% inVideoPath = [inVideoDir 'shadows.avi'];
% inTimestampPath = [inVideoDir '2-hours.txt'];

% output
outBackgroundPath = [CITY_DATA_PATH 'camdata/cam572/5pm/models/refBackground.png'];
outVideoPath = [inVideoDir 'models/adjBackground.avi'];
outBackimage = [inVideoDir 'models/backimage.png'];
refBackImage = imread(outBackgroundPath);

doWrite = true;


% objects to detect background, to read video, and to write results video
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
background.fp_level = 0;
background.fn_level = 0;
frameReader = FrameReaderVideo (inVideoPath, inTimestampPath);
if doWrite, frameWriter = FrameWriterVideo (outVideoPath, 2, 1); end

for t = 1 : 10000
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % subtract background and return mask
    mask = background.subtract(frame);
    
    % increase the mask size
    DilateRadius = 0;
    seDilate = strel('disk', DilateRadius);
    mask = imdilate(mask, seDilate);
    
    if ~exist('backImage', 'var')
        backImage = frame;
    end
    
    % paint the unmasked part of the image
    kNew = 0.3;
    maskColor = mask(:,:,[1,1,1]);
    backImage(~maskColor) = frame(~maskColor) * kNew + backImage(~maskColor) * (1 - kNew);
    
    % adjust the reference background with backImage
    adjBackImage = generateCleanBackground(refBackImage, backImage, ...
        'verbose', 0);
    
    if doWrite, frameWriter.writeNextFrame(adjBackImage); end

    imshow([frame, adjBackImage]);
    pause (0.1);
    
end

if doWrite, imwrite (adjBackImage, outBackimage); end

% need to clear frameWriter to complete writing video file
clear frameReader frameWriter
