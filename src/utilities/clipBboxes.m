function clippedBBoxes = clipboxes(bboxes, im)
% Clip detection windows to image the boundary.
%   ROIs = clipboxes(ROIs, im)
%
%   All boxes are trimmed so that they are within the image area.
%
%   ROIs    A set of ROI in the format N x [x1 y1 x2+1 y2+1]
%   im      Image for the boxes. Only its size is used


assert (isempty(bboxes) || size(bboxes,2) == 4);

if isempty(bboxes)
    return
end

clippedBBoxes = [];

for i = 1 : size(bboxes,1)
    bbox = bboxes(i,:);
    
    % if completely out of borders, skip
    if bbox(1) + bbox(3) <= 1 || bbox(1) > size(im,2) || ...
       bbox(2) + bbox(4) <= 1 || bbox(2) > size(im,1)
        continue;
    end
    
    bbox(1) = max(bbox(1), 1);
    bbox(2) = max(bbox(2), 1);
    bbox(3) = min(bbox(3) + bbox(1), size(im,2) + 1) - bbox(1);
    bbox(4) = min(bbox(4) + bbox(2), size(im,1) + 1) - bbox(2);
    
    clippedBBoxes = [clippedBBoxes; bbox];
end
