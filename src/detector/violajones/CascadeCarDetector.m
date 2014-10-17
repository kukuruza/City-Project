% viola-jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorInterface
    properties (Hidden)
        detector; % vision.CascadeObjectDetector
    end % properties
    methods
        function CD = CascadeCarDetector (modelPath)
            CD.detector = vision.CascadeObjectDetector(modelPath);
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