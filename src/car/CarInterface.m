% interface for car

classdef CarInterface < handle
    methods (Abstract)
        
        % compute ROI from car bbox
        roi = getROI (C);  % [y1, x1, y2, x2]
        
        % compute appearance feature (HoG, color, etc) and save it
        generateFeature (C, image);
        
        % compute the center of the bbox
        center = getCenter (C) % [y x]

        % draw car on an image
        im = drawCar (C, im)
        
    end % methods
end