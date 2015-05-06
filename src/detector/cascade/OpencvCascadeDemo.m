if ~exist ('cv.m', 'file')
    error ('Please install OpenCV package and add it to your search path');
end

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

model_path = [CITY_DATA_PATH 'violajones/opencv/cascade.xml'];
detector = cv.CascadeClassifier(model_path);

%bboxes = detector.detectMultiScale(img);