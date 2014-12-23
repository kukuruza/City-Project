% interface for car

classdef CarInterface < handle
    methods (Abstract)
        
        % constructor
        % Car(bbox, timestamp = [0 0 0 0 0 0]);
        
        % compute ROI from car bbox
        roi = getROI (C);  % [y1, x1, y2, x2]
        
        % patch is a crop of the car from the provided image
        % parameters:
        %   'segment' {'none', 'maxflow', 'background'}, default is 'none'
        patch = extractPatch (C, image, parameters)
        
        % compute the center of the bbox
        center = getCenter (C) % [y x]
        
        % compute the center of the bottom of the bbox
        center = getBottomCenter (C) % [y x]

        % draw car on an image with (optionally) specified tag and color
        % parameters:
        %  'color', default is 'yellow'
        %  'tag', default is 'car'
        %  'boxOpacity', default is 0.6
        im = drawCar (C, image, parameters)
        
    end % methods
end