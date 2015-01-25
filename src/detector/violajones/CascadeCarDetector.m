% Matlab Viola-Jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorBase
    properties %(Hidden)
        
        verbose;
        
        % debugging - filtering by size
        noFilter = false;
        
        geometry;
        roi;   % roi in an image for the detector
        sizeMap;

        mask;

        %grayThreshold;
        
        % vision.CascadeObjectDetector
        detector;
        modelPath;
        
    end % properties
    methods
        function CD = CascadeCarDetector (modelPath, geometry, varargin)
            global CITY_DATA_PATH;
            assert (~isempty(CITY_DATA_PATH));
            parser = inputParser;
            addRequired(parser, 'modelPath', @(x) ischar(x) && exist([CITY_DATA_PATH x], 'file'));
            addRequired(parser, 'geometry', @(x) isa(x, 'GeometryInterface'));
            addParameter(parser, 'minsize', [15 20], @(x) isvector(x) && length(x) == 2);
            addParameter(parser, 'maxsize', [150 200], @(x) isvector(x) && length(x) == 2);
            addParameter(parser, 'scaleFactor', 1.1, @isscalar);
            addParameter(parser, 'mergeThreshold', 3, @isscalar);
            addParameter(parser, 'mask', [], @ismatrix);
            addParameter(parser, 'verbose', 0, @isscalar);
%            addParameter(parser, 'grayThreshold', 0, @isscalar);
            parse (parser, modelPath, geometry, varargin{:});
            parsed = parser.Results;
            
            CD.verbose = parsed.verbose;
            CD.geometry = geometry;
            CD.sizeMap = CD.geometry.getCameraRoadMap();
%            CD.grayThreshold = parsed.grayThreshold;
            if ~isempty(parsed.mask)
                assert (all(size(parsed.mask) == size(CD.sizeMap)));
                CD.mask = parsed.mask;
            else
                CD.mask = true(size(CD.sizeMap));
            end

            % find the mask for the detector
            CD.roi = mask2roi (CD.sizeMap > 0 & CD.mask);
            assert (~isempty(CD.roi));
            
            CD.modelPath = modelPath;
            CD.detector = vision.CascadeObjectDetector([CITY_DATA_PATH modelPath], ...
                'MinSize', parsed.minsize, ...
                'MaxSize', parsed.maxsize, ...
                'ScaleFactor', parsed.scaleFactor, ...
                'MergeThreshold', parsed.mergeThreshold);
            
        end
        
        
        function mask = getMask(CD)
            mask = CD.mask;
        end
        
 
        function setVerbosity (CD, verbose)
            CD.verbose = verbose;
        end
        

        function cars = detect (CD, img)
            if CD.verbose > 1, fprintf ('CascadeCarDetector\n'); end

            orientationMap = CD.geometry.getOrientationMap();

            % crop the image to the non-masked area for a cluster
            img = img(CD.roi(1) : CD.roi(3), CD.roi(2) : CD.roi(4));

            bboxes = step(CD.detector, img);
            cars = [];
            for i = 1 : size(bboxes,1)
                car = Car(bboxes(i,:));
                
                % compensate for the crop
                car.addOffset (CD.roi(1:2) - 1);

                pos = car.getBottomCenter();

                % assign orientation to the car
                car.orientation = [orientationMap.yaw(pos(1), pos(2)), ...
                                   orientationMap.pitch(pos(1), pos(2))];
                
                if CD.mask(pos(1), pos(2))
                    cars = [cars; car];
                end
            end
            
            % filter by size
            if ~CD.noFilter
                cars = CD.filterCarsBySize (cars, CD.sizeMap, 'verbose', CD.verbose);
            end
        end
        
        
    end % methods 
    methods (Static)
        function obj = loadobj(obj)
            % make detector model path user independent
            global CITY_DATA_PATH;
            assert (~isempty(CITY_DATA_PATH));
            obj.detector.ClassificationModel = [CITY_DATA_PATH, obj.modelPath];
        end
    end
end
