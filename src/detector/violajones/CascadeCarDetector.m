% Matlab Viola-Jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorInterface
    properties (Hidden)
        
        geometry;
        
        % applicability of the model
        minsize;
        maxsize;
        
        grayThreshold;
        
        % vision.CascadeObjectDetector
        detector; 
        
    end % properties
    methods
        function CD = CascadeCarDetector (modelPath, geometry, varargin)
            parser = inputParser;
            addRequired(parser, 'modelPath', @(x) ischar(x) && exist(x, 'file'));
            addRequired(parser, 'geometry', @(x) isa(x, 'GeometryInterface'));
            addParameter(parser, 'minsize', [15 20], @(x) isvector(x) && length(x) == 2);
            addParameter(parser, 'maxsize', [150 200], @(x) isvector(x) && length(x) == 2);
            addParameter(parser, 'scaleFactor', 1.1, @isscalar);
            addParameter(parser, 'mergeThreshold', 3, @isscalar);
%            addParameter(parser, 'grayThreshold', 0, @isscalar);
            parse (parser, modelPath, geometry, varargin{:});
            parsed = parser.Results;
            
            CD.geometry = parsed.geometry;
            CD.minsize = parsed.minsize;
            CD.maxsize = parsed.maxsize;
%            CD.grayThreshold = parsed.grayThreshold;
            
            CD.detector = vision.CascadeObjectDetector(parsed.modelPath, ...
                'MinSize', CD.minsize, ...
                'MaxSize', CD.maxsize, ...
                'ScaleFactor', parsed.scaleFactor, ...
                'MergeThreshold', parsed.mergeThreshold);
            
        end
        function cars = detect (CD, img)
            orientationMap = CD.geometry.getOrientationMap();
            sizeMap = CD.geometry.getCameraRoadMap();

            bboxes = step(CD.detector, img);
            cars = [];
            for i = 1 : size(bboxes,1)
                car = Car(bboxes(i,:));
                pos = car.getBottomCenter();
                
                % assign orientation to the car
                car.orientation = [orientationMap.yaw(pos(1), pos(2)), ...
                                   orientationMap.pitch(pos(1), pos(2))];
                
                % filter based on size 
                if sizeMap(pos(1), pos(2))
                    cars = [cars; car];
                end
            end
        end
    end % methods
end
