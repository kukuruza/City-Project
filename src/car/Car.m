% This class is primarily for halping CarDetector classes to provide
%   more verbose output: besides the bounding box, the class may store
%   any additional information like size, orientation, etc.
%

classdef Car < CarInterface
    properties
        bbox;  % [x1 y1 width height]
        patch = [];
        segmentMask;
        
        % parameters
        timeStamp; % time of the frame. [yyyy mm dd hh mm ss]. sec. is float
        orientation; % [yaw pitch]
        
    end % propertioes
    methods (Hidden)
        function segmentMaxflow (C)
            assert (~isempty(C.patch));
            
            % actual segmentation
            UnariesOffset = 0.4;
            EdgeWeight = 0.2;
            mask = segmentWrapper(C.patch, UnariesOffset, EdgeWeight);
            
            % remove small artefacts from mask
            ArtefactSize = 5;
            mask = bwareaopen (mask, ArtefactSize^2);
            C.segmentMask = mask;
        end
    end % Hidden

    methods
        function C = Car(varargin) % see interface
            % parse and validate input
            parser = inputParser;
            addRequired (parser, 'bbox', @(x) isvector(x) && length(x) == 4);
            addOptional (parser, 'timestamp', [0 0 0 0 0 0], ...
                                         @(x) isvector(x) && length(x) == 6);
            parse (parser, varargin{:});

            C.bbox = parser.Results.bbox;
            C.timeStamp = parser.Results.timestamp;
        end
        
        
        function roi = getROI (C)  % [y1, x1, y2, x2]
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
        end
        
                                
        function patch = extractPatch (C, image, varargin)
            % parse and validate input
            parser = inputParser;
            addRequired (parser, 'image', @(x) ndims(x)==3 && size(x,3)==3);
            expectedSegmentation = {'none', 'maxflow', 'background'};
            addParameter (parser, 'segment', 'none', ...
                          @(x) any(validatestring(x,expectedSegmentation)));
            parse (parser, image, varargin{:});
            
            % extract patch
            roi = C.getROI();
            C.patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
            patch = C.patch;
            
            % segment if required
            if strcmp(parser.Results.segment, 'maxflow')
                C.segmentMaxflow();
            end
        end
        
        
        function center = getCenter (C) % [y x]
            center = [int32(C.bbox(2) + C.bbox(4) / 2), ...
                      int32(C.bbox(1) + C.bbox(3) / 2)];
        end
        
        
        function center = getBottomCenter (C) % [y x]
            center = [int32(C.bbox(2) + C.bbox(4) - 1), ...
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
