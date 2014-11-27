% A simple tutorial script to demonstrate the use of Geometry class for
% various functionalities

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run ../rootPathsSetup.m
run ../subdirPathsSetup.m

imageDir = [CITY_DATA_PATH '2-min/camera360'];
imageName = 'image0000.jpg';
filePath = fullfile(imageDir, imageName);

%Reading the image and marking points
image = imread(filePath);

% Loading the road properties that were manually marked (Pts for the lanes)
%matFile = 'Geometry_Camera_360.mat';
%geom = GeometryEstimator(image, matFile);
%fprintf ('GeometryEstimator: constructor finished\n');

% Geometry object can be simply loaded using the object file
% The object geom will be directly loaded. However, newer functionalities
% might need this object to be created again
objectFile = 'GeometryObject_Camera_360.mat';
load(objectFile);
fprintf(strcat('Read Geometry object from file, might not be the latest version\n' , ...
   'Update if made changes to GeometryEstimator class\n'));

%geom.road.drawLanesOnImage(image);

%setting the image size for the geometry module
laneMask = geom.getRoadMask();

%Fetch the camera road map for various sizes of the cars expected
cameraRoadMap = geom.getCameraRoadMap();

%% Check size [and lane] estimation for every point on the road

roadPoints = ...  % [x y]
[109 186; ...     % car in the 4th lane in the front
 157 143; ...     % car in the 4th lane faraway
 210 139; ...     % car in the 4th lane faraway
 300 200; ...     % not a road
 100 100 ...     % not a road
];

carWidths = [50 20 20 0 0];

carLanes = [4 4 5 0 0];

for i = 1 : size(roadPoints,1)
    fprintf ('car width at point #%d, estimate: %f, truth: %f\n', ...
        i, carWidths(i), cameraRoadMap(roadPoints(i,2), roadPoints(i,1)));
end


%% Check the probability calculating module given two cars 
%   Cars are taken from cam360, image0045 and image0048
% Choose any two cars from below list of points
% rois   = N x [x1 y1 x2 y2] - easier to get
% bboxes = N x [x y width height]
rois = ...
[84 172 132 200; ...   % 1: first detection of the real car in 4th lane
 186 126 200 136; ...  % 2: second detection of the real car in 4th lane
 134 122 147 130; ...  % 3: normal dist, but on the 1st lane (should be ~0)
 149 125 164 134; ...  % 4: normal dist, but on the 2nd lane (should be ~0)
 167 126 182 137; ...  % 5: normal dist, but on the 3rd lane (should be small)
 209 126 223 135; ...  % 6: normal dist, but on the 5th lane (should be small)
 158 145 176 158; ...  % 7: car is in the 4th lane, but passed only half dist. 
 34 199 82 234 ...    % 8: car is moved in opposite direction (should be 0)
];
bboxes = [rois(:,1:2) rois(:,3)-rois(:,1) rois(:,4)-rois(:,2)];

% ground truth
mutualProb = {'n/a', 'high', '~0', '~0', 'small', 'small', 'smaller', '==0'};

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

return;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Displaying the probability heat maps for visualization for all these
% points

for i = 1:size(bboxes, 1)
 car = Car(bboxes(i, :));
 [probHeatMap, overLaidImg] = geom.generateProbMap(car, frameDiff, image);
 figure; imshow(overLaidImg)
end

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
