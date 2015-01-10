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

% output
outBackgroundPath = [inVideoDir 'models/refBackground.png'];
outVideoPath = [inVideoDir 'models/adjBackground.avi'];
doWrite = false;
refBackImage = imread(outBackgroundPath);

% objects to detect background, to read video, and to write results video
%background = BackgroundGMM ('fn_level', 15, 'fp_level', 1);
load ([CITY_DATA_PATH 'camdata/cam572/5pm/models/backgroundGMM.mat']);
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
        'fgThreshold', 40, 'verbose', 1);
    
    if doWrite, frameWriter.writeNextFrame(adjBackImage); end

    %subplot(1,2,1);
    %imshow(mask);
    %subplot(1,2,2);
    %imshow(backImage);
    %imshow([backImage, 255 * mask(:,:,[1 1 1])])
    %pause(0.5)
    
end

% need to clear frameWriter to complete writing video file
clear frameReader frameWriter
