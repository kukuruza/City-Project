function trainCascade (posDirPath, negDirPath, outModelPath, imsize)
% trainCascade trains a Viola-Jones model.
%   it uses positive samples and negative images from provided directories


% output model path
[~, modelName, ext] = fileparts(outModelPath);
modelName = [modelName ext];


% get positive filenames
imTemplate = [posDirPath, '*.png']; % matlab requires jpg or png
imNames = dir (imTemplate);

% create an array of structures 
posData = struct('imageFilename','', 'objectBoundingBoxes',[]);
for i = 1 : length(imNames)
    
    posData(i).imageFilename = [posDirPath imNames(i).name];
    % read patch to know its dimensions
    patch = imread(posData(i).imageFilename);
    posData(i).objectBoundingBoxes = [1 1 size(patch,2) size(patch,1)];
    
end

trainCascadeObjectDetector(modelName, posData, negDirPath, ...
    'FalseAlarmRate', 0.15, ...
    'NumCascadeStages', 5, ...
    'ObjectTrainingSize', imsize, ...
    'NegativeSamplesFactor', 5, ...
    'FeatureType', 'Haar' ...
    );

% move trained model
movefile(modelName, fileparts(outModelPath));


