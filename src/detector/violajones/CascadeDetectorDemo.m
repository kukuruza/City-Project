% detect object using trained cascade classifier

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'



%% input

%imPath = '../testdata/10am-064.jpg';
imPath = '../testdata/5pm-018.png';
img = imread(imPath);
thresh = 2;
mask = abs(img(:,:,1) - 128) < thresh & ...
       abs(img(:,:,2) - 128) < thresh & ...
       abs(img(:,:,3) - 128) < thresh;
img(mask(:,:,[1 1 1])) = 128;

verbose = 0;


%% detect and refine

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.getCameraRoadMap();

modelPath = [CITY_DATA_PATH, 'violajones/models/model03-cr10.xml'];
minsize = [30 40];

detector = CascadeCarDetector(modelPath, geom, 'minsize', minsize);

tic
cars = detector.detect(img);
toc

for i = 1 : length(cars)
    img = cars(i).drawCar(img, 'color', 'blue');
end


% filtering cars based on sizes
SizeTolerance = 1.5;
counter = 1;
carsFilt = Car.empty;
for k = 1 : length(cars)
    center = cars(k).getBottomCenter(); % [y x]
    expectedSize = roadCameraMap(center(1), center(2));
    fprintf('expectedSize: %f ', expectedSize);
    fprintf('actualSize: %f\n', cars(k).bbox(3));
    if expectedSize / SizeTolerance < cars(k).bbox(3) && ...
       expectedSize * SizeTolerance > cars(k).bbox(3)
        carsFilt(counter) = cars(k);
        counter = counter + 1;
    end
end
fprintf ('kept %d out of %d cars.\n', length(carsFilt), length(cars));
cars = carsFilt;    


for i = 1 : length(cars)
    img = carsFilt(i).drawCar(img);
end

% show detector's mask
if verbose
    bbox = roi2bbox(mask2roi(detector.sizeMap > 0));
    img = insertObjectAnnotation(img, 'rectangle', bbox, 'sizeMap bbox', 'Color', 'blue');
    mask = detector.sizeMap > 0;
    img = img + 50 * uint8(mask(:,:,[1 1 1]));
end

figure(1)
imshow(img);




