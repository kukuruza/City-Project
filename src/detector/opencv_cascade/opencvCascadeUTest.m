if ~exist ('cv.m', 'file')
    error ('Please install OpenCV package and add it to your search path');
end

run '../../rootPathsSetup.m';
%run '../../subdirPathsSetup.m'

model_path = [CITY_DATA_PATH 'violajones/opencv/cascade.xml'];
detector = cv.CascadeClassifier(model_path);

%bboxes = detector.detectMultiScale(img);