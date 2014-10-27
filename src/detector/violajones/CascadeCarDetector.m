% viola-jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorInterface
    properties (Hidden)
        scaleWindow = 1.5; % maxSize / minSize
        detector; % vision.CascadeObjectDetector
    end % properties
    methods
        function CD = CascadeCarDetector (modelPath, avgsize)
            assert (isvector(avgsize) && length(avgsize) == 2);
            minsize = [18 36];
            maxsize = [30 60];
            CD.detector = vision.CascadeObjectDetector(modelPath, ...
                'MinSize', minsize, 'MaxSize', maxsize);
        end
        function cars = detect (CD, img)
            bboxes = step(CD.detector, img);
            cars = [];
            for i = 1 : size(bboxes,1)
                cars = [cars; Car(bboxes(i,:))];
            end
        end
    end % methods
end