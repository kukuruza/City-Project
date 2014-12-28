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


% objects to detect background, to read video, and to write results video
background = BackgroundGMM ('fn_level', 15, 'fp_level', 1);
frameReader = FrameReaderVideo (inVideoPath, inTimestampPath);
frameWriter = FrameWriterVideo (outVideoPath, 2, 1);

for t = 1 : 10000
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % subtract background and return mask
    mask = background.subtract(frame);
    
    % increase the mask size
    DilateRadius = 2;
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
    rBackImage(~mask) = rFrame(~mask);
    gBackImage(~mask) = gFrame(~mask);
    bBackImage(~mask) = bFrame(~mask);
    backImage = cat(3, rBackImage, gBackImage, bBackImage);
    
    frameWriter.writeNextFrame(backImage);

    imshow(backImage);
    pause(0.3)
    
end
    
% need to clear frameWriter to complete writing video file
clear frameReader frameWriter
