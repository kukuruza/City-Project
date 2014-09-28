function expandedROIs = expandboxes(ROIs, perc, im)
% Clip detection windows to image the boundary.
%   ROIs = clipboxes(ROIs, im)
%
%   All boxes are trimmed so that they are within the image area.
%
%   ROIs    A set of ROI in the format N x [x1 y1 x2+1 y2+1]
%   im      Image for the boxes. Only its size is used


% parameters validatation
assert (isempty(ROIs) || size(ROIs,2) == 4);
assert (isscalar(perc));
assert (ndims(im) >= 2);
assert (isa(ROIs, 'int32'));

expandedROIs = ROIs;

if isempty(ROIs)
    return
end

for i = 1 : size(ROIs,1)
    roi = ROIs(i,:);
    
    width  = roi(3) - roi(1);
    height = roi(4) - roi(2);
    roi = roi + int32([ -width * perc, -height * perc, width * perc, height * perc]);
    
    expandedROIs(i,:) = roi;
end

expandedROIs = clipboxes(expandedROIs, im);

