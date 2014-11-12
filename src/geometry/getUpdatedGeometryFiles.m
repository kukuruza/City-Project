% Script to update all the mat files to reflect any changes made in the
% related classes. These mat files can be directly loaded in the pipeline
% to debug other modules; thus avoiding longer initializations each time.

% Instead of creating a 'geom' object in the pipeline, read corresponding
% GeometryObject_Camera_x.mat file to get geom loaded into the workspace

clear all
run ../rootPathsSetup.m
run ../subdirPathsSetup.m

cameraNumber = [360, 368, 572];
for i = 1:3
    cameraStr = num2str(cameraNumber(i));
    imageDir = [CITY_DATA_PATH strcat('2-min/camera', cameraStr)];
    imageName = 'image0000.jpg';
    filePath = fullfile(imageDir, imageName);

    %Reading the image and marking points
    image = imread(filePath);
    
    % Loading the road properties that were manually marked (Pts for the lanes)
    matFile = strcat('Geometry_Camera_', cameraStr, '.mat');
    geom = GeometryEstimator(image, matFile);
    fprintf ('GeometryEstimator for camera %s: constructor finished\n', cameraStr);
    
    save(strcat('GeometryObject_Camera_', cameraStr, '.mat'), 'geom');
end