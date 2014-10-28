% This class is primarily for halping CarDetector classes to provide
%   more verbose output: besides the bounding box, the class may store 
%   any additional information like size, orientation, etc.
%

classdef Car < CarInterface
    properties
        bbox;  % [x1 y1 width height]
        patch = [];
        
        % features
        timeStamp; %Time stamp for the car
        feature = [];

    end % propertioes
    methods
        function C = Car (bbox, timestamp)
            %Assigning a default value to timeStamp
            if(nargin < 2)
                timestamp = [1 2 3 4 5 6]; 
            end
            C.bbox = bbox;
            C.timeStamp = timestamp;
        end
        
        function roi = getROI (C)  % [y1, x1, y2, x2]
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
        end
        
        function extractPatch (C, image)
            roi = C.getROI();
            C.patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
        end
        
        function generateFeature (C, image)
            C.extractPatch(image);
            % logic
            % TODO: implement
        end
        
        function center = getCenter (C) % [y x]
            center = [int32(C.bbox(2) + C.bbox(4) / 2), ...
                      int32(C.bbox(1) + C.bbox(3) / 2)];
        end
        
        function im = drawCar (C, im)
            im = insertObjectAnnotation(im, 'rectangle', C.bbox, 'car');
        end
        
    end % methods
end
