function newbboxes = addOffset2Boxes (bboxes, offset)
% addOffset2Boxes adds an offset [x0 y0] to every box from  N x [x1 y1 width height]

% parameter validation
assert (isvector(offset) && length(offset) == 2);
assert (isempty(bboxes) || (ismatrix(bboxes) && size(bboxes,2) == 4));

newbboxes = [bboxes(:,1) + offset(1), bboxes(:,2) + offset(2), ...
             bboxes(:,3), bboxes(:,4)];

            
