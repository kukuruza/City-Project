% Prepare positive images for detection:
%   crop the image, make grayscale, rescale
%
% Written primarily for CBCL database of 128x128 images


clear all;

% crop size from images
crop_height = 64;
crop_width = 96;
% destination (rescaled) size
dst_height = 30;
dst_width = 40;


% setup data directory
run '../../rootPathsSetup.m';

global CITY_DATA_PATH;
imagesDirIn = [CITY_DATA_PATH, 'violajones/cbcl/cars128x128/'];
imagesDirOut = [CITY_DATA_PATH, 'violajones/cbcl/patches_positive/'];
ext = '.ppm';


% get the filenames
imTemplate = [imagesDirIn, '*', ext];
imNames = dir (imTemplate);

for i = 1 : length(imNames)
    imName = imNames(i);
    
    % read
    im = imread([imagesDirIn, imName.name]);
    
    % to grayscale
    if ndims(im) == 3
        im = rgb2gray(im);
    end
    
    % crop
    sz = size(im);
    height = sz(1);
    width = sz(2);
    assert (height >= crop_height && width >= crop_width);
    im = im ((height - crop_height)/2 : (height + crop_height)/2, ...
             (width - crop_width)/2 : (width + crop_width)/2);

    % scale
    im = imresize(im, [dst_height, dst_width]);
    
    % write
    imwrite(im, [imagesDirOut, imName.name]);
end
    