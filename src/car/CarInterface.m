% interface for car

classdef CarInterface < handle
    methods (Abstract)
        
        % compute ROI from car bbox
        roi = getROI (C);  % [y1, x1, y2, x2]
        
        % patch is a crop of the car from the provided image
        patch = extractPatch (C, image)
        
        % compute appearance feature (HoG, color, etc) and save it
        generateFeature (C, image);
        
        % compute the center of the bbox
        center = getCenter (C) % [y x]
        
        % compute the center of the bottom of the bbox
        center = getBottomCenter (C) % [y x]

        % draw car on an image with (optionally) specified tag and color
        im = drawCar (C, im, color, tag)
        
    end % methods
end