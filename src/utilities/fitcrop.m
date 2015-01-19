function crop = fitcrop (image, roi)
% intelligently crop input image, cropping less than requested
%   if the crop is out of the borders

parser = inputParser;
addRequired(parser, 'image', @(x) ismatrix(x) || iscolorimage(x));
addRequired(parser, 'roi', @(x) isvector(x) && length(x) == 4);
parse (parser, image, roi);

crop = image (max(1,roi(1)) : min(size(image,1),roi(3)), ...
              max(1,roi(2)) : min(size(image,2),roi(4)), ...
              :);

