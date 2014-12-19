% interface for car

classdef CarInterface < handle
    methods (Abstract)
        
        % constructor
        % Car(bbox, timestamp = [0 0 0 0 0 0]);
        
        % compute ROI from car bbox
        roi = getROI (C);  % [y1, x1, y2, x2]
        
        % patch is a crop of the car from the provided image
        % 
        % parameters define segmentation method if any. Its syntax is:
        %   extractPatch(..., 'segment', 'maxflow'/'background')
        patch = extractPatch (C, image, parameters)
        
        % compute the center of the bbox
        center = getCenter (C) % [y x]
        
        % compute the center of the bottom of the bbox
        center = getBottomCenter (C) % [y x]

        % draw car on an image with (optionally) specified tag and color
        im = drawCar (C, im, color, tag)
        
    end % methods
end