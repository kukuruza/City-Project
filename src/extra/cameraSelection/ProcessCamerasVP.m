% Script to process the selected cameras from the images dumped

% setup all the paths
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;

%cameraList = [119, 123, 141, 152, 196, 197, 233, 448, 449, ...
%                450, 482, 543, 572, 573, 577, 578, 645, 656,...
%                666, 671, 672, 685, 687, 715];
% Final camera geometry list
%finalList = [119, 123, 196, 233, 448, 449, 450, 482, 543, 572, 573, 577, ...
%            578, 656, 685, 715];
            
% Pruned list = [448, 449, 450, 482, 543, 578, 666, 671, 672, 687];
prunedList = [448, 449, 450, 482, 543, 578, 666, 671, 672, 687];

% Starting from camera 577
%sizes = [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4 0.4, ];
%sizes = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, ...
%                1.0, 1.0, 1.0, 1.0, 1.0, 0.4, 0.4, 0.4, 0.4,...
%                0.4, 0.4, 0.4, 0.4, 0.4, 1.0];
%outputPath = 'dumpFolder/';
%load('GeometryObject_Camera_572.mat');

for i = 15:length(cameraList)
    % Creating the file name
    cameraId = cameraList(i);
    imagePath = [CITY_DATA_PATH '2-min/camdata/cam', num2str(cameraId), '/'];
    
    % Preparing the camera files for parfor
    %noImages = length(dir(fullfile(imagePath, '*.png')));
    % We want only first 10 images
    noImages = 10;
   
    % Parallel for cells
    frames = cell(noImages, 1);
    grayFrames = cell(noImages, 1);
    roadImages = cell(noImages, 1);
    displayImages = cell(noImages, 1);

    % Preparing the images
    for j = 1:noImages
        imageName = fullfile(imagePath, sprintf('image%04d.png', j));
        frames{j} = imread(imageName);
        grayFrames{j} = rgb2gray(frames{j});   
    end
    
    parfor t = 1:noImages
        % Debugging the vanishing point detection
        scale = sizes(i);
        grayImg = imresize(grayFrames{t}, scale);
        colorImg = imresize(frames{t}, scale);
        norient = 36;

        numOfValidFiles = t;

        tic; 
        [vanishPt, orientationMap] = ...
            geom.detectVanishingPoint(grayImg, colorImg, norient, ...
                                    outputPath, numOfValidFiles);
        toc;

        [roadImg, displayImg] = ...
            geom.detectRoadBoundary(grayImg, colorImg, vanishPt, orientationMap, ...
                                    outputPath, numOfValidFiles); 

        %vanishPoints{t} = vanishPt;
        roadImages{t} = roadImg;
        displayImages{t} = displayImg;
        %figure(1); imshow(displayImg)
    end
    imagePath = fullfile('binary', sprintf('cam%d', cameraId));
    % Creating the folder if it doesnt exists
    if(~exist(imagePath, 'dir'))
        mkdir(imagePath)
    end
    
    for j = 1 : noImages
        imageName = fullfile(imagePath, sprintf('%04d.png', j));
        imwrite(roadImages{j}, imageName);
    end
    
    imagePath = fullfile('output', sprintf('cam%d', cameraId));
    % Creating the folder if it doesnt exists
    if(~exist(imagePath, 'dir'))
        mkdir(imagePath)
    end     
    
    for j = 1 : noImages
        imageName = fullfile(imagePath, sprintf('%04d.png', j));
        imwrite(displayImages{j}, imageName);
    end
end