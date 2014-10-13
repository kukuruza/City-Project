% viola-jones implementation of CarDetectorInterface

classdef CascadeCarDetector < CarDetectorInterface
    properties (Hidden)
        detector; % vision.CascadeObjectDetector
    end % properties
    methods
        function CD = CascadeCarDetector (modelPath)
            CD.detector = vision.CascadeObjectDetector(modelPath);
        end
        function bboxes = detect (CD, img)
            bboxes = step(CD.detector, img);
        end
    end % methods
end