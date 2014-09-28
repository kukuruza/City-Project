function clippedROIs = clipboxes(ROIs, im)
% Clip detection windows to image the boundary.
%   ROIs = clipboxes(ROIs, im)
%
%   All boxes are trimmed so that they are within the image area.
%
%   ROIs    A set of ROI in the format N x [x1 y1 x2+1 y2+1]
%   im      Image for the boxes. Only its size is used


assert (isempty(ROIs) || size(ROIs,2) == 4);

if isempty(ROIs)
    return
end

clippedROIs = [];

for i = 1 : size(ROIs,1)
    roi = ROIs(i,:);
    
    % if completely out of borders, skip
    if roi(3) <= 1 || roi(4) <= 1 || roi(1) > size(im,2) || roi(2) > size(im,1)
        continue;
    end
    
    roi(1) = max(roi(1), 1);
    roi(2) = max(roi(2), 1);
    roi(3) = min(roi(3), size(im,2)+1);
    roi(4) = min(roi(4), size(im,1)+1);
    
    clippedROIs = [clippedROIs; roi];
end
