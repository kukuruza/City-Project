% Matlab Viola-Jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorInterface
    properties (Hidden)
        
        geometry;
        orientationMap;
        
        % applicability of the model
        minsize = [15 20];
        maxsize = [150 200];
        modelOrientation = [];
        modelMask = [];
        
        detector; % vision.CascadeObjectDetector
    end % properties
    methods
        function CD = CascadeCarDetector (modelPath, geometry, sizemap, orientation)
            CD.detector = vision.CascadeObjectDetector(modelPath, ...
                'MinSize', CD.minsize, 'MaxSize', CD.maxsize, ...
                'MergeThreshold', 3);
            
            CD.geometry = geometry;
            %CD.orientationMap = CD.geometry.getOrientationMap();

            if nargin > 3
                CD.modelMask = (sizemap > mean(CD.minsize) | sizemap < mean(CD.maxsize));
            end
            if nargin > 2
                CD.modelOrientation = orientation;
            end
        end
        function cars = detect (CD, img)
            bboxes = step(CD.detector, img);
            cars = [];
            for i = 1 : size(bboxes,1)
                car = Car(bboxes(i,:));
                pos = car.getBottomCenter();
                
                % assign orientation to the car
                if ~isempty(CD.geometry)
                    %car.orientation = CD.orientationMap(pos(1), pos(2));
                end
                
                % filter based on size 
                % TODO: and based on orientation
                if isempty(CD.modelMask) || CD.modelMask(pos(1), pos(2))
                    cars = [cars; car];
                end
            end
        end
    end % methods
end
