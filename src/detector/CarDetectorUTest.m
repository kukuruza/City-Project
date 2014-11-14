% detect object using trained cascade classifier

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../rootPathsSetup.m';
run '../subdirPathsSetup.m'



%% input

imPath = [CITY_DATA_PATH, 'testdata/detector/img000.jpg'];
img0 = imread(imPath);



%% ground truth

trueBboxes = dlmread([CITY_DATA_PATH, 'testdata/detector/img000.txt']);




%% detect and refine

modelPath = [CITY_DATA_PATH, 'violajones/models/model1.xml'];

detector = CascadeCarDetector(modelPath);

tic
cars = detector.detect(img0);
toc

img = img0;
for i = 1 : length(cars)
    img = insertObjectAnnotation(img, 'rectangle', cars(i).bbox, 'car');
end
figure (1);
imshow(img);

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.getCameraRoadMap();


% filtering cars based on sizes
SizeTolerance = 1.5;
counter = 1;
carsFilt = Car.empty;
for k = 1 : length(cars)
    center = cars(k).getCenter(); % [y x]
    expectedSize = roadCameraMap(center(1), center(2));
    fprintf('expectedSize: %f ', expectedSize);
    fprintf('actualSize: %f\n', cars(k).bbox(3));
    if expectedSize / SizeTolerance < cars(k).bbox(3) && ...
       expectedSize * SizeTolerance > cars(k).bbox(3)
        carsFilt(counter) = cars(k);
        counter = counter + 1;
    end
end
cars = carsFilt;    


img = img0;
for i = 1 : length(carsFilt)
    img = insertObjectAnnotation(img, 'rectangle', carsFilt(i).bbox, 'car');
end
figure (2);
imshow(img);





