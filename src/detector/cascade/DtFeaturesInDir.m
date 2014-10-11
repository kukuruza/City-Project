% This script extracts features from all the images in a directory
%   and saves them as variable 'features' in a specified file

clear all

% setup data directory
run '../rootPathsSetup.m';

global CITY_DATA_PATH;
%global CITY_DATA_LOCAL_PATH;

% patches dir
imagesDirIn = [CITY_DATA_PATH, 'violajones/cbcl/patches_negative/cam360/'];
% output features name
featureFileOut = [CITY_DATA_PATH, 'violajones/cbcl/features/hog-4x3-eq/neg.mat'];


% get the filenames
imTemplate = [imagesDirIn, '*.ppm'];
imNames = dir (imTemplate);

featuresCell = cell (length(imNames),1);
for i = 1 : length(imNames)
    imName = imNames(i);
    
    % read
    img = imread([imagesDirIn, imName.name]);
    
    % extract features
    feature = extractFeature (img);
    
    % save
    featuresCell {i} = feature;
end

% rewrite as a matrix instead of a cell array
features = [];
if ~isempty(featuresCell)
    features = zeros(length(featuresCell), length(featuresCell{1}));
    for i = 1 : length(featuresCell)
        features(i,:) = featuresCell{i};
    end
end


% write resulting feature to a variable
save(featureFileOut, 'features');

