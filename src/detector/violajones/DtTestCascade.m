% detect object using trained cascade classifier

run '../../rootPathsSetup.m';

% test images dir
imagesDir = [CITY_DATA_PATH, 'violajones/testdata/images/'];
modelPath = [CITY_DATA_PATH, 'violajones/models/model1.xml'];

% load model
detector = vision.CascadeObjectDetector(modelPath);

% detect
imPath = [imagesDir 'cam368_0080.jpg'];
img = imread(imPath);

bboxes = step(detector, img);
detectedImg = insertObjectAnnotation(img, 'rectangle', bboxes, 'car');
figure; imshow(detectedImg);
