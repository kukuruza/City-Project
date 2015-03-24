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
inVideoDir = [CITY_DATA_PATH 'camdata/cam671/'];
inVideoPath = [inVideoDir 'Mar24-12h.avi'];
inTimestampPath = [inVideoDir 'Mar24-12h.txt'];
% inVideoDir = [CITY_DATA_PATH 'camdata/cam572/10am/'];
% inVideoPath = [inVideoDir 'shadows.avi'];
% inTimestampPath = [inVideoDir '2-hours.txt'];

% output
%refBackgroundPath = [inVideoDir 'models/backimage.png'];
%refBackImage = imread(refBackgroundPath);
outVideoPath = [inVideoDir 'models/Mar24-12h-background.avi'];
outBackimagePath = [inVideoDir 'models/Mar24-12h-backimage.png'];

doWrite = true;
doShow = false;


% objects to detect background, to read video, and to write results video
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
background.fp_level = 0;
background.fn_level = 0;
frameReader = FrameReaderVideo (inVideoPath, inTimestampPath);
if doWrite, frameWriter = FrameWriterVideo (outVideoPath, 2, 1); end

for t = 1 : 100
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % subtract background and return mask
    mask = background.subtract(frame);
    
    % increase the mask size
    DilateRadius = 1;
    seDilate = strel('disk', DilateRadius);
    mask = imdilate(mask, seDilate);
    
    if ~exist('backImage', 'var')
        backImage = frame;
    end
    
    % paint the unmasked part of the image
    kNew = 0.2;
    maskColor = mask(:,:,[1,1,1]);
    backImage(~maskColor) = frame(~maskColor) * kNew + backImage(~maskColor) * (1 - kNew);
    
    % adjust the reference background with backImage
    %adjBackImage = generateCleanBackground(refBackImage, backImage, ...
    %    'verbose', 0);
    %backImage = adjBackImage;

    if doWrite, frameWriter.writeNextFrame(backImage); end

    if doShow
        imshow([frame, backImage]);
        pause ();
    end
    
end

if doWrite, imwrite (backImage, outBackimagePath); end

% need to clear frameWriter to complete writing video file
clear frameReader frameWriter
