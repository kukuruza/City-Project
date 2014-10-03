function expandedBBoxes = expandboxes(bboxes, perc, im)
% Clip detection windows to image the boundary.
%   ROIs = clipboxes(ROIs, im)
%
%   All boxes are trimmed so that they are within the image area.
%
%   ROIs    A set of ROI in the format N x [x1 y1 x2+1 y2+1]
%   im      Image for the boxes. Only its size is used


% parameters validatation
assert (isempty(bboxes) || size(bboxes,2) == 4);
assert (isscalar(perc));
assert (ndims(im) >= 2);
assert (isa(bboxes, 'int32'));

expandedBBoxes = bboxes;

if isempty(bboxes)
    return
end

for i = 1 : size(bboxes,1)
    bbox = bboxes(i,:);
    bbox = bbox + int32([ -bbox(3) * perc, -bbox(4) * perc, ...
                          bbox(3) * perc, bbox(4) * perc]);
    
    expandedBBoxes(i,:) = bbox;
end

expandedBBoxes = clipBboxes(expandedBBoxes, im);

