% learn PCA of car appearance features
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% setup all the paths
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

% input cars
inCarsDir = [CITY_DATA_PATH 'testdata/detector/detections/'];
carsList = dir([inCarsDir '*car*.mat']);

% all features in one matrix
poolHog = [];
poolCol = [];

for i = 1 : length(carsList)

    % load car object
    clear car
    load ([inCarsDir carsList(i).name]);
    
    % generate features and combine them into one
    car.generateFeature();
    
    % lazy initialization (after when we know the size of pools)
    if isempty(poolHog)
        poolHog = zeros(length(carsList), length(car.histHog));
        poolCol = zeros(length(carsList), length(car.histCol));
    end
    
    poolHog(i, :) = car.histHog;
    poolCol(i, :) = car.histCol;
end

% do PCA
[coeff,score,~,~,explained,offset] = pca(poolHog, 'NumComponents',80);
save('pcaColor.mat', 'coeff', 'explained', 'offset');
[coeff,score,~,~,explained,offset] = pca(poolCol);
save('pcaHog.mat',   'coeff', 'explained', 'offset');

