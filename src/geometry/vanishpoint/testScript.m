clear all;
close all;

% My paths
inputPath = '~/CMU/VanishingPointEstimation/image%03d.jpg'; %%% input image path
outputPath_final = '~/CMU/VanishingPointEstimation/results/'; %%% result path

vpCoord = [];
%imSize = [180, 240];

%imgName = sprintf(inputPath, 106);
   imgName = '~/CMU/VanishingPointEstimation/image0000.jpg';
    
if exist(imgName,'file')>0
    colorImg = imread(imgName);
    if size(colorImg,3)>1
       img = rgb2gray(colorImg);
    else
        img = colorImg;
    end

    img = imresize(img, size(img));%[180, 240]); 
    colorImg = imresize(colorImg, size(img));
    
    tic
    i = 35;
    % Their implementation
    tic; args = author(img,colorImg, 36, outputPath_final, i); toc
    
    % My implementation
    % Running it as a script
    grayImg = img;
    colorImg = colorImg;
    norient = 36;
    outputPath = outputPath_final;
    numOfValidFiles = 35;
    %tic; faster(grayImg, colorImg, norient, outputPath, numOfValidFiles) ; toc
    tic; faster ; toc
end

