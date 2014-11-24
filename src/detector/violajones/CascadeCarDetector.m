% Matlab viola-jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorInterface
    properties (Hidden)
        
        % applicability of the model
        minsize = [15 20];
        maxsize = [150 200];
        orientation = [];
        mask = [];
        
        detector; % vision.CascadeObjectDetector
    end % properties
    methods
        function CD = CascadeCarDetector (modelPath, sizemap, orientation)
            CD.detector = vision.CascadeObjectDetector(modelPath, ...
                'MinSize', CD.minsize, 'MaxSize', CD.maxsize);
            
            if nargin > 2
                CD.mask = (sizemap > mean(CD.minsize) | sizemap < mean(CD.maxsize));
            elseif nargin > 2
                CD.orientation = orientation;
            end
            
        end
        function cars = detect (CD, img)
            bboxes = step(CD.detector, img);
            cars = [];
            for i = 1 : size(bboxes,1)
                car = Car(bboxes(i,:));
                
                % filter based on size
                pos = car.getBottomCenter();
                if isempty(CD.mask) || CD.mask(pos(1), pos(2))
                    cars = [cars; car];
                end
            end
        end
    end % methods
end
