function expandedBBoxes = expandBboxes(bboxes, perc, im)
%EXPANDBBOXES Expand bboxes and clip detection windows to image boundaries
%
%   bboxes = N x [x y w h]
%   perc - to add to all four sides
%   im - Image for the boxes. Only its size is used


% parameters validatation
assert (isempty(bboxes) || size(bboxes,2) == 4);
assert (isscalar(perc));
assert (ndims(im) >= 2);

expandedBBoxes = double(bboxes);

if isempty(bboxes)
    return
end

for i = 1 : size(bboxes,1)
    bbox = bboxes(i,:);
    bbox = bbox + [ -bbox(3) * perc, -bbox(4) * perc, ...
                     bbox(3) * 2 * perc, bbox(4) * 2 * perc];
    
    expandedBBoxes(i,:) = bbox;
end

expandedBBoxes = clipBboxes(expandedBBoxes, im);

