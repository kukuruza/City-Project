function im = showCarboxes(im, car)
% Draw bounding boxes on top of an image.
%   showboxes(im, boxes, out)
%
%   If out is given, a pdf of the image is generated (requires export_fig).

assert (size(car.bboxes,1) >= 1);

for i = 1 : size(car.bboxes,1)
    if i == 1
      c = [255 0 0];
    else
      c = [0 255 0];
    end
    im = drawRect(im, int32(car.bboxes(i,:)), c);
end
