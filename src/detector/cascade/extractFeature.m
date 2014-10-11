function featureVect = extractFeature (patch)
%%GETFEATURE - get a vector [1 n] of some feature from an input image
%
% featureVect = extractFeature (im, mask, gridHalfSize, enlargeBox, verbose)
%
% patch - color/grayscale image


%% feature specific constants
% a patch is cut into cells of side cellsize.
cellsize = 10;


%% verify input
assert (ismatrix(patch) || (ndims(patch) == 3 && size(patch,3) == 3));

  
%% get hog. Specific to HoG feature

if ~exist('vl_hog', 'file')
    error ('Hello Lynna, please install VLFeat or run VLFEATROOT/toolbox/vl_setup');
end

featureVect = vl_hog (single(patch), double(cellsize));
featureVect = reshape(featureVect, [1, numel(featureVect), 1]);




