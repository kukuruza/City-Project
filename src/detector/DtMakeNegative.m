% The script collects negative examples for the car detector training
%   The source of the negative patches are images from cameras. The patches
%   are collected from the road area (using provided road masks)
%   from the background (as estimated by background substraction)
%
% Thus, the full pipeline is taking many camera frames, extracting the
%   background, taking the road mask, and generate some patches. A number
%   of patches is taken from every frame.
%

clear all

% maximunm intersection with smth positive, that is still considered neg.
maxInters = 0.5;
halfSizeMin = 5;
halfSizeMax = 25;

% destination (rescaled) size
dst_height = 30;
dst_width = 40;

% number of patches from a camera
enoughPatches = 10;


% camera
camName = 'cam360';

% setup data directory
run '../rootPathsSetup.m';
run '../subdirPathsSetup.m';

global CITY_DATA_PATH;
%global CITY_DATA_LOCAL_PATH;

imagesDirOut = [CITY_DATA_PATH, 'violajones/cbcl/patches_negative/', camName, '/'];
camMaskFile = [CITY_DATA_PATH, 'roadMasks/', camName, '.png'];
camMask = logical(imread(camMaskFile));


frameReader = FrameReaderImages(); 
subtractor = BackgroundSubtractor(5, 30);

counter = 0;
while 1
    % read image
    img = frameReader.getNewFrame();
    if isempty(img), break, end
    if (ndims(img) == 3), img = rgb2gray(img); end
    
    % subtract background and return mask
    % bboxes = N x [x1 y1 width height]
    [foregroundMask, bboxes] = subtractor.subtract(img);

    backgroundMask = ~foregroundMask & camMask;
    
    
    counterbreak = 0;
    counterFrame = 0;
    while counterFrame < enoughPatches && counterbreak < enoughPatches * 10
        a = (randi(halfSizeMax-halfSizeMin) + halfSizeMin);
        y = randi(size(img,1));
        x = randi(size(img,2));
                
        if y-a > 0 && y+a-1 < size(img,1) && x-a > 0 && x+a-1 < size(img,2)
            if sum(sum( backgroundMask(y-a : y+a-1, x-a : x+a-1) )) > a^2 * 4 * maxInters
                patch = img (y-a : y+a-1, x-a : x+a-1, :);
                
                % scale
                patch = imresize(patch, [dst_height, dst_width]);

                % equalize
                patch = histeq(patch);

                % write
                imwrite (patch, [imagesDirOut, 'car_', sprintf('%04d', counter), '.ppm']);
                
                counter = counter + 1;
                counterFrame = counterFrame + 1;
            end
        end

        % if smth weird happens, stop break cycle
        counterbreak = counterbreak + 1;
    end

    
end