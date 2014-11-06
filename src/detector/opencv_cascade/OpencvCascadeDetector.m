% Matlab viola-jones implementation of CarDetectorInterface

classdef OpencvCascadeDetector < CarDetectorInterface
    properties (Hidden)
        model_path = [CITY_DATA_PATH 'violajones/opencv/cascade.xml'];
        detector; % OpenCV detector
    end % properties
    methods
        function CD = OpencvCascadeDetector ()
            CD.detector = cv.CascadeClassifier(modelPath); % FIXME: find out
        end
        function cars = detect (CD, img)
            bboxes = CD.detector.detectMultiScale(img); % FIXME: make sure
            cars = [];
            for i = 1 : size(bboxes,1)
                cars = [cars; Car(bboxes(i,:))];
            end
        end
    end % methods
end
