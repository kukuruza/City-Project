% Prepare positive and negative patches for detection:
%   crop the image, make grayscale, rescale
%
% Positives are cropped in the center of an image, negatives - around the
%   center, so that the intersection with positives is small
%
% Written primarily for CBCL database of 128x128 images


clear all;

% do historgram equalization
doHistEqual = false;

% number of negatives for each positive
NegNumber = 10;
% number of maximum tries to get a negative with accepatable intersection
NegBreakNumber = 100;
% max acceptable intersection
MaxIntersThresh = 0.5;
MinIntersThresh = 0.25;

% crop size from images [height, width]
positive_sz = [64 96];
negative_szs = uint32([0.5; 0.7; 1] * positive_sz);
% destination (rescaled) size
dst_sz = [30 40];

% output prefix
outPrefix = 'cbcl';


% setup data directory
run '../../rootPathsSetup.m';

global CITY_DATA_PATH;
global CITY_SHARED_DATA_PATH;
imagesDirIn = [CITY_SHARED_DATA_PATH, 'violajones/cbcl/cars128x128/'];
patchesDirPosOut = [CITY_DATA_PATH, 'violajones/cbcl/patches/positive_nequ/'];
patchesDirNegOut = [CITY_DATA_PATH, 'violajones/cbcl/patches/negative_nequ/'];


% get the filenames
imTemplate = [imagesDirIn, '*.ppm'];
imNames = dir (imTemplate);

patchcounter = 1;
for i = 1 : length(imNames)
    imName = imNames(i);
    
    % read
    img = imread([imagesDirIn, imName.name]);
    
    % to grayscale
    if ndims(img) == 3
        img = rgb2gray(img);
    end
    
    % image size
    sz = size(img);
    height = sz(1);
    width = sz(2);

    % crop positive
    crop_height = positive_sz(1);
    crop_width = positive_sz(2);
    assert (height >= crop_height && width >= crop_width);
    l1 = (width - crop_width) / 2;
    r1 = (width + crop_width) / 2;
    t1 = (height - crop_height) / 2;
    b1 = (height + crop_height) / 2;
    patch_pos = img (t1 : b1, l1 : r1);
         
    % crop a few negatives
    patches_neg = {};
    counter = 1;
    for j = 1 : NegBreakNumber
        if counter > NegNumber, break, end
        crop_sz = negative_szs(randi(length(negative_szs)), :);
        crop_height = crop_sz(1);
        crop_width = crop_sz(2);
        t2 = randi ([1, height - crop_height - 1]);
        l2 = randi ([1, width - crop_width - 1]);
        b2 = t2 + crop_height;
        r2 = l2 + crop_width;
        tint = max(t1, t2);
        bint = min(b1, b2);
        lint = max(l1, l2);
        rint = min(r1, r2);
        % if 1) pospatch intersects with negpatch 
        %    2) pospatch has enough area with and without intersection, 
        %    3) negpatch has enough area with and without intersection
        areaInters = double((bint-tint) * (rint-lint));
        areaPos = double((b1-t1) * (r1-l1));
        areaNeg = double((b2-t2) * (r2-l2));
        fprintf ('i/p = %f, i/n = %f \n', areaInters/areaPos, areaInters/areaNeg);
        if tint < bint && lint < rint && ...
                 areaInters / areaPos > MinIntersThresh && ...
                 areaInters / areaPos < MaxIntersThresh && ...
                 areaInters / areaNeg > MinIntersThresh && ...
                 areaInters / areaNeg < MaxIntersThresh
            patches_neg{counter} = img(t2 : b2, l2 : r2);
            counter = counter + 1;
        end
    end

    % scale
    patch_pos = imresize(patch_pos, dst_sz);
    for j = 1 : length(patches_neg)
        patches_neg{j} = imresize(patches_neg{j}, dst_sz);
    end
    
    % equalize
    if doHistEqual == true
        patch_pos = histeq(patch_pos);
        for j = 1 : length(patches_neg)
            patches_neg{j} = histeq(patches_neg{j});
        end
    end
    
    % write
    imPosNum = sprintf('%04d', patchcounter);
    patchcounter = patchcounter + 1;
    imwrite(patch_pos, [patchesDirPosOut outPrefix '_' imPosNum '.png']);
    for j = 1 : length(patches_neg)
        imNegNum = sprintf('%04d', patchcounter);
        patchcounter = patchcounter + 1;
        imwrite(patches_neg{j}, [patchesDirNegOut outPrefix '_' imNegNum '.png']);
    end
end
    