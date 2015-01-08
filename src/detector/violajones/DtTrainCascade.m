% train the Viola-Jones classifier from positive and negative patches


%clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';

% patches dir
patchesPosDirIn = [CITY_DATA_PATH, 'violajones/patches/pos-01/'];
patchesNegDirIn = [CITY_DATA_PATH, 'violajones/patches/neg-t7/'];

% output model path
outModelPath = [CITY_DATA_PATH, 'violajones/models/model-01-t7.xml'];
[~, modelName, ext] = fileparts(outModelPath);
modelName = [modelName ext];

% get positive filenames
imTemplate = [patchesPosDirIn, '*.png']; % matlab requires jpg or png
imNames = dir (imTemplate);

% create an array of structures 
posData = struct('imageFilename','', 'objectBoundingBoxes',[]);
for i = 1 : length(imNames)
    
    posData(i).imageFilename = [patchesPosDirIn imNames(i).name];
    % read patch to know its dimensions
    patch = imread(posData(i).imageFilename);
    posData(i).objectBoundingBoxes = [1 1 size(patch,2) size(patch,1)];
    
end

trainCascadeObjectDetector(modelName, posData, patchesNegDirIn, ...
    'FalseAlarmRate', 0.15, ...
    'NumCascadeStages', 5, ...
    'ObjectTrainingSize', [15 20], ...
    'NegativeSamplesFactor', 5, ...
    'FeatureType', 'Haar' ...
    );

% move trained model
movefile(modelName, fileparts(outModelPath));

