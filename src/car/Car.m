% This class is primarily for halping CarDetector classes to provide
%   more verbose output: besides the bounding box, the class may store
%   any additional information like size, orientation, etc.
%

classdef Car < CarInterface
    properties
        bbox;  % [x1 y1 width height]
        patch = [];
        
        % features
        timeStamp; % the time the frame was taken. [yyyy mm dd hh mm ss]. sec. is float
        feature = [];
        histHog = [];
        histCol = [];
        
    end % propertioes
    methods
        function C = Car (bbox, timestamp)
            C.bbox = bbox;
            
            if (nargin < 2)
                % assigning a default value to timeStamp
                C.timeStamp = [];
            else
                C.timeStamp = timestamp;
            end
        end
        
        
        function roi = getROI (C)  % [y1, x1, y2, x2]
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
        end
        
        
        function patch = extractPatch (C, image)
            roi = C.getROI();
            C.patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
            patch = C.patch;
        end
        
        
        function generateFeature (C)
            
            % must call C.extractPatch() before
            assert (~isempty(C.patch));
            
            % Hog Feature
            HOG = vl_hog(single(imresize(C.patch, [24 24])), 12);
            C.histHog = reshape(HOG, 1, numel(HOG));
            C.histHog = C.histHog / sum(C.histHog(:)); % normalize, better for all probabilistic methods
            
            % Color Feature
            r = mean(mean(C.patch(:,:,1)));
            g = mean(mean(C.patch(:,:,2)));
            b = mean(mean(C.patch(:,:,3)));
            C.histCol = [r g b];
                                  
        end
        
        
        function center = getCenter (C) % [y x]
            center = [int32(C.bbox(2) + C.bbox(4) / 2), ...
                int32(C.bbox(1) + C.bbox(3) / 2)];
        end
        
        
        function im = drawCar (C, im, color, tag, boxOpacity)
            if nargin < 3, color = 'yellow'; end
            if nargin < 4, tag = 'car'; end
            if nargin < 5, boxOpacity = 0.6; end
            if boxOpacity > 0.5
                textColor = 'black';
            else
                textColor = 'white';
            end
            %color = 128 + rand(1,3) * 127;
            im = insertObjectAnnotation(im, 'rectangle', C.bbox, ...
                tag, 'Color', color, ...
                'TextBoxOpacity', boxOpacity, 'TextColor', textColor, ...
                'FontSize', 12);
        end
        
    end % methods
end
