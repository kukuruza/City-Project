function roi = mask2roi (mask)

assert (ismatrix(mask));
assert (islogical(mask));

% empty mask
if nnz(mask) == 0, roi = []; return, end

obj = regionprops(mask, 'BoundingBox');
bbox = obj.BoundingBox;

roi = [bbox(2)+0.5, bbox(1)+0.5, bbox(2)+bbox(4)-0.5, bbox(1)+bbox(3)-0.5];
roi = uint32(roi);
