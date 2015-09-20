% This class is primarily for halping CarDetector classes to provide
%   more verbose output: besides the bounding box, the class may store
%   any additional information like size, orientation, etc.
%

classdef Car < CarInterface
    properties
        bbox  % [x1 y1 width height]
        patch
        
        name;
        timestamp % time of the frame. Format is string
        yaw
        pitch
        color
        
        % detection score
        score
        
    end % propertioes

    methods
        function self = Car(varargin) % see interface
            % parse and validate input
            parser = inputParser;
            addParameter (parser, 'bbox', [], @(x) isempty(x) || isvector(x) && length(x) == 4);
            addParameter (parser, 'timestamp', '', @ischar);
            addParameter (parser, 'name', 'vehicle', @ischar);
            addParameter (parser, 'score', [], @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;

            self.bbox      = parsed.bbox;
            self.timestamp = parsed.timestamp;
            self.name      = parsed.name;
            self.score     = parsed.score;
        end
        
        
        function patch = extractPatch (self, image, varargin)
            % parse and validate input
            parser = inputParser;
            addRequired (parser, 'image', @iscolorimage);
            parse (parser, image, varargin{:});
            
            % extract patch
            roi = self.getROI();
            self.patch = image(roi(1) : roi(3), roi(2) : roi(4), :);
            patch = self.patch;
        end
        
        
        function center = getCenter (self) % [y x]
            center = [int32(self.bbox(2) + self.bbox(4) / 2), ...
                      int32(self.bbox(1) + self.bbox(3) / 2)];
        end
        
        
        function center = getBottomCenter (self) % [y x]
            HeightRatio = 0.75;
            center = [int32(self.bbox(2) + self.bbox(4) * HeightRatio - 1), ...
                      int32(self.bbox(1) + self.bbox(3) / 2)];  % why is it -1 ???
        end
        
        
        function addOffset (self, offset)
            assert (isvector(offset) && length(offset) == 2);
            self.bbox(1) = self.bbox(1) + int32(offset(2));  % x
            self.bbox(2) = self.bbox(2) + int32(offset(1));  % y
        end

        
        function im = drawCar (self, im, varargin)
            % parse and validate input
            parser = inputParser;
            addRequired (parser, 'im', @(x) ndims(x)==3 && size(x,3) == 3);
            addParameter (parser, 'color', 'yellow');
            addParameter (parser, 'fontsize', 12);
            addParameter (parser, 'tag', '', @ischar);
            addParameter (parser, 'boxOpacity', 0.6, @(x) isnumeric(x) && isscalar(x));
            parse (parser, im, varargin{:});
            parsed = parser.Results;

            if parsed.boxOpacity > 0.5, textColor = 'black'; else textColor = 'yellow'; end
            %color = 128 + rand(1,3) * 127;
            if isempty(parsed.tag), tag = self.name; else tag = parsed.tag; end
            im = insertObjectAnnotation(im, 'rectangle', self.bbox, tag, ...
                'Color', parsed.color, ...
                'TextBoxOpacity', parsed.boxOpacity, ...
                'TextColor', textColor, ...
                'FontSize', parsed.fontsize);
        end
        
    end % methods
end
