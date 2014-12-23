clear all;
close all;

% My paths
inputPath = '~/CMU/VanishingPointEstimation/image%03d.jpg'; %%% input image path
outputPath_final = '~/CMU/VanishingPointEstimation/results/'; %%% result path

vpCoord = [];

%imgName = sprintf(inputPath, 106);
   imgName = '~/CMU/VanishingPointEstimation/image106.jpg';
    
if exist(imgName,'file')>0
    colorImg = imread(imgName);
    if size(colorImg,3)>1
       img = rgb2gray(colorImg);
    else
        img = colorImg;
    end

    %imSize = [180, 240];
    imSize = 0.5 * size(img);
    %imSize = [90, 120];
    img = imresize(img, imSize);%[180, 240]); 
    colorImg = imresize(colorImg, imSize);
    
    i = 35;
    % Their implementation
    %tic; args = author(img,colorImg, 36, outputPath_final, i); toc
    
    % My implementation
    % Running it as a script
    grayImg = img;
    colorImg = colorImg;
    norient = 36;
    outputPath = outputPath_final;
    numOfValidFiles = 35;
    
    tic; 
    [vanishPt, orientationMap] = ...
        detectVanishingPoint(grayImg, colorImg, norient, ...
                                outputPath, numOfValidFiles);
    toc
    
    tic;
    [roadImg, displayImg] = ...
        detectRoadLanes(grayImg, colorImg, vanishPt, orientationMap, ...
                                outputPath, numOfValidFiles); 
    toc
    
    figure(1); imshow(displayImg)
end

