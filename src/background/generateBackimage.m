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
outBackgroundPath = [inVideoDir 'models/background.png'];
outVideoPath = [inVideoDir 'models/backgroundTry.avi'];
doWrite = false;


% objects to detect background, to read video, and to write results video
%background = BackgroundGMM ('fn_level', 15, 'fp_level', 1);
load ('/Users/evg/projects/City-Project/data/camdata/cam572/5pm/models/backgroundGMM.mat')
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
        backImage = uint8(zeros(size(frame)));
    end
    
    rBackImage = backImage(:,:,1);
    gBackImage = backImage(:,:,2);
    bBackImage = backImage(:,:,3);
    
    % paint the unmasked part of the image
    rFrame = frame(:,:,1);
    gFrame = frame(:,:,2);
    bFrame = frame(:,:,3);
    kNew = 0.3;
    rBackImage(~mask) = rFrame(~mask) * kNew + rBackImage(~mask) * (1 - kNew);
    gBackImage(~mask) = gFrame(~mask) * kNew + gBackImage(~mask) * (1 - kNew);
    bBackImage(~mask) = bFrame(~mask) * kNew + bBackImage(~mask) * (1 - kNew);
    backImage = cat(3, rBackImage, gBackImage, bBackImage);
    
    if doWrite, frameWriter.writeNextFrame(backImage); end

    subplot(1,2,1);
    imshow(mask);
    subplot(1,2,2);
    imshow(backImage);
    pause(0.1)
    
end
    
% need to clear frameWriter to complete writing video file
clear frameReader frameWriter
