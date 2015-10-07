% Matlab Viola-Jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorBase
    properties %(Hidden)
        
        mask; % mask of detector applicability
        
        cropPercent; % how much to crop (ViolaJones are train with expanded bboxes)
        
        detector; % vision.CascadeObjectDetector
        
    end % properties
    methods
        function self = CascadeCarDetector (modelPath, varargin)
            parser = inputParser;
            addRequired(parser, 'modelPath', @(x) ischar(x) && exist(fullfile(getenv('CITY_DATA_PATH'), x), 'file'));
            addParameter(parser, 'minsize', [18 24], @(x) isvector(x) && length(x) == 2);
            addParameter(parser, 'maxsize', [150 200], @(x) isvector(x) && length(x) == 2);
            addParameter(parser, 'scaleFactor', 1.1, @isscalar);
            addParameter(parser, 'mergeThreshold', 3, @isscalar);
            addParameter(parser, 'cropPercent', 0, @isscalar);
            addParameter(parser, 'mask', [], @ismatrix);
            parse (parser, modelPath, varargin{:});
            parsed = parser.Results;
            
            self.cropPercent = parsed.cropPercent;
            self.mask = parsed.mask;
            self.detector = vision.CascadeObjectDetector(...
                fullfile(getenv('CITY_DATA_PATH'), modelPath), ...
                'MinSize', parsed.minsize, ...
                'MaxSize', parsed.maxsize, ...
                'ScaleFactor', parsed.scaleFactor, ...
                'MergeThreshold', parsed.mergeThreshold);
        end
        
        function cars = detect (self, img)
            if self.verbose > 1, fprintf ('CascadeCarDetector\n'); end
            if isempty(self.mask), self.mask = true(size(img,1),size(img,2)); end
            bboxes = step(self.detector, img);
            bboxes = expandBboxes(bboxes, -self.cropPercent, img);  % crop bboxes
            cars = [];
            for i = 1 : size(bboxes,1)
                car = Car('bbox', bboxes(i,:), 'score', 1);
                pos = car.getBottomCenter();
                if self.mask(pos(1), pos(2))
                    cars = [cars; car];
                end
            end
        end
        
    end % methods 
    methods (Static)
        function obj = loadobj(obj)
            obj.detector.ClassificationModel = fullfile(getenv('CITY_DATA_PATH'), obj.modelPath);
        end
    end
end
