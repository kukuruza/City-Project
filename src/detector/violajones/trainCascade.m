function trainCascade (posDirPath, negDirPath, outModelPath, imsize, varargin)
% trainCascade trains a Viola-Jones model.
%   it uses positive samples and negative images from provided directories

parser = inputParser;
addRequired(parser, 'posDirPath', @(x) ischar(x) && exist(x, 'dir'));
addRequired(parser, 'negDirPath', @(x) ischar(x) && exist(x, 'dir'));
addRequired(parser, 'outModelPath', @(x) ischar(x) && exist(fileparts(x), 'dir'));
addRequired(parser, 'imsize', @(x) isvector(x) && length(x) == 2);
addParameter(parser, 'crop', 0, @(x) isscalar(x) && x >= 0 && x < 0.5);
parse (parser, posDirPath, negDirPath, outModelPath, imsize, varargin{:});
parsed = parser.Results;

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
    sz = size(patch);
    
    % calculate the bbox from dimentions and crop
    crop = parsed.crop;
    bbox = uint32([sz(2) * crop, sz(1) * crop, sz(2) * (1-2*crop), sz(1) * (1-2*crop)]);
    
    posData(i).objectBoundingBoxes = bbox;
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


