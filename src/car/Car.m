% This class is primarily for halping CarDetector classes to provide
%   more verbose output: besides the bounding box, the class may store 
%   any additional information like size, orientation, etc.
%

classdef Car
    properties
        bbox  % [x1 y1 width height]
    end % propertioes
    methods
        function C = Car (bbox)
            C.bbox = bbox;
        end
        function roi = getROI (C)
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
        end
    end % methods
end
