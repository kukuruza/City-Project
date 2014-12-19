% A simple tutorial script to demonstrate the use of Geometry class for
% various functionalities 
% Also tests these for camera 572 

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run ../../rootPathsSetup.m
run ../../subdirPathsSetup.m

imageDir = [CITY_DATA_PATH 'geometry'];
imageName = 'img000.jpg';
filePath = fullfile(imageDir, imageName);
textPath = strrep(filePath, '.jpg', '.txt');

% Grouth truth bounding boxes
gtBboxes = dlmread(textPath, ',');

%Reading the image and marking points
image = imread(filePath);

% Loading the road properties that were manually marked (Pts for the lanes)
%matFile = 'Geometry_Camera_360.mat';
%geom = GeometryEstimator(image, matFile);
%fprintf ('GeometryEstimator: constructor finished\n');

% Geometry object can be simply loaded using the object file
% The object geom will be directly loaded. However, newer functionalities
% might need this object to be created again
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf(strcat('Read Geometry object from file, might not be the latest version\n' , ...
   'Update if made changes to GeometryEstimator class\n'));

%geom.road.drawLanesOnImage(image);

%setting the image size for the geometry module
laneMask = geom.getRoadMask();

%Fetch the camera road map for various sizes of the cars expected
cameraRoadMap = geom.getCameraRoadMap();


%% Check size [and lane] estimation for every point on the road
% Using the ground truths, get the position of the car
% Compare the ground truth with the estimated width

for i = 1 : 1%size(gtBboxes,1)
    % Extracting the position of the car on the road and its size
    box = gtBboxes(i, :);
    carPos = floor([box(1) + box(3)/2, box(2) + box(4)]);
    carSize = box(3);
    
    fprintf ('Car width at point #%d, Ground: %f, Estimate: %f\n', ...
        i, box(3), cameraRoadMap(carPos(2), carPos(1)));
end


% %% Check the probability calculating module given two cars 
% %   Cars are taken from cam572, images 004 and 005
% % Choose any two cars from below list of points
% % rois   = N x [x1 y1 x2 y2] - easier to get
% % bboxes = N x [x y width height]

% Car 1 : Lane 2, in front of car 2
% Car 2 : Lane 2, behind car 1
% Car 3 : Lane 3, in front of car 4
% Car 4 : Lane 3, in front of car 3
% Ground truth boxes for frame 1(image 004)
cars1 = ...
[247, 180, 42, 39; ...
202, 225, 64, 40; ...
213, 165, 28, 23; ...
160, 182, 54, 43];

% Cars in frame 2
cars2 = ...
[221, 199, 64, 53; ...
139, 274, 92, 72; ...
184, 180, 42, 30; ...
48, 222, 104, 80];

% Other random rois which we want to check our estimator with
rois = ...
[440, 205 65 35; ... % 1: Point on a lane travelling on different direction; 
                      %should result in zero
237, 151, 18, 15; ... % 2: Car behind all the other cars; should result in zero
];

% ground truth of the probabilities
% First we compare cars with each other and then with additional roi
% Comparing (1)
mutualProb = {'0', 'high', ...
    '~0', '~0', 'small', 'small', 'smaller', '==0'};

car1Ind = 1;
car2Ind = 2;
frameDiff = 1;

% Obtain the mutual probabilites 1 to i
car1 = Car(bboxes(1, :));
for i = 2 : size(bboxes,1)
    car2 = Car(bboxes(i, :));
    prob = geom.getMutualProb(car1, car2, frameDiff);
    fprintf('probability to move from 1 to %d, estimate: %f, truth: %s \n', ...
        i, prob, mutualProb{i});
end

% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % Displaying the probability heat maps for visualization for all these
% % points
% % for i = 1:size(bboxes, 1)
% %     car = Car(bboxes(i, :));
% %     [probHeatMap, overLaidImg] = geom.generateProbMap(car, frameDiff, image);
% %     figure; imshow(overLaidImg)
% % end
% 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
