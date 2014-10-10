% A simple tutorial script to demonstrate the use of Geometry class for
% various functionalities

%Directory and image name to load up a toy image
imageDir = '~/CMU/5-camera-for-2-hours/cameraNumber360-part1';
imageName = 'image0.jpg';
filePath = fullfile(imageDir, imageName);

%Reading the image and marking points
image = imread(filePath);

% Loading the road properties that were manually marked (Pts for the lanes)
% Default for camera 360 marked within the constructor for
% GeometryEstimator()
%matFile = 'Geometry_Camera_360.mat';
geom = GeometryEstimator();

%setting the image size for the geometry module
fprintf('Road mask generated from lanes\n');
geom.imageSize = [size(image, 1), size(image, 2)];
geom.getRoadMask();

%Fetch the camera road map for various sizes of the cars expected
cameraRoadMap = geom.getCameraRoadMap();

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Checking the probability calculating module given two cars (choose any two
%cars from below list of random points)
pts = [50 151 97 124 197 237 217 306; 177 135 176 187 167 126 203 161];
index = [1 1 2 3 4 5 5];

car1Ind = 1;
car2Ind = 2;
frameDiff = 1;

bbox1 = [pts(1, car1Ind) pts(2, car1Ind) 0 0];
bbox2 = [pts(1, car2Ind) pts(2, car2Ind) 0 0];

car1 = Car(bbox1);
car2 = Car(bbox2);

%Obtain the mmutual 
probability = geom.getMutualProb(car1, car2, frameDiff);
fprintf('Estimated probability for given two cars: %f\n', probability);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Displaying the results
%figure; imagesc(geom.roadMask);
%figure; imagesc(geom.getCameraRoadMap());

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Testing the road module seperately.
%road = Road(matFile);
% markedImg = road.drawLanesOnImage(image);
% imshow(markedImg)
%return
%pts = [50 151 97 124 197 237 217 306; 177 135 176 187 167 126 203 161];
%index = [1 1 2 3 4 5 5];
% for i = 1:size(pts, 2)
%     bbox = [pts(1, i) pts(2, i) 0 0];
%     car = Car(bbox);
%     index = [index; road.detectCarLane(car)];
%     fprintf('%d %d => %d \n', pts(1, i), pts(2, i), index(end));
% end