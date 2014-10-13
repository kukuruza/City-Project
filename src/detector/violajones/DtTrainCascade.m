% train the Viola-Jones classifier from positive and negative patches

run '../../rootPathsSetup.m';

% patches dir
patchesPosDirIn = [CITY_DATA_PATH, 'violajones/preprocessed/positive/'];
patchesNegDirIn = [CITY_DATA_PATH, 'violajones/preprocessed/negative_44x33/'];

% output model path
outModelName = 'model1.xml';  % matlab forbids using its full path

% get positive filenames
imTemplate = [patchesPosDirIn, '*.png']; % matlab requires jpg
imNames = dir (imTemplate);

% create an array of structures 
posData = struct('imageFilename','', 'objectBoundingBoxes',[]);
for i = 1 : length(imNames)
    
    posData(i).imageFilename = [patchesPosDirIn imNames(i).name];
    % read patch to know its dimensions
    patch = imread(posData(i).imageFilename);
    posData(i).objectBoundingBoxes = [1 1 size(patch,2) size(patch,1)];
    
end

trainCascadeObjectDetector(outModelName, posData, patchesNegDirIn, ...
    'FalseAlarmRate', 0.9, 'NumCascadeStages', 5);
