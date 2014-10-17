% class for holding general car info
%

classdef CarAppearance
    properties
        iFrame;
        feature = [];
        bbox  % [x1 y1 width height]
    end
    methods
        function C = CarAppearance (bbox, iFrame)
            C.iFrame = iFrame;
            C.bbox = bbox;
        end
        function roi = getROI (C)  % [y1, x1, y2, x2]
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
        end
        function patch = extractPatch (C, image)
            roi = C.getROI();
            patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
        end
        function generateFeature (C, image)
            patch  = C.extractPatch(image);
            % logic
            C.feature = [];  % TODO: implement
        end
    end % methods
end