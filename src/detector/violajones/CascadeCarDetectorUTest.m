% detect object using trained cascade classifier

clear all

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'

% test images dir
imagesDir = [CITY_DATA_PATH, 'violajones/testdata/images/'];
modelPath = [CITY_DATA_PATH, 'violajones/models/model1.xml'];

detector = CascadeCarDetector(modelPath);

% detect
imPath = [imagesDir 'cam368_0080.jpg'];
img = imread(imPath);

cars = detector.detect(img);
for i = 1 : length(cars)
    img = insertObjectAnnotation(img, 'rectangle', cars(i).bbox, 'car');
end
figure; imshow(img);
