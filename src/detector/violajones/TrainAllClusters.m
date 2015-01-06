% Train a cascade for each cluster
% 


clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';



%% input

posList = [1, 2, 3, 4, 5, 6];
negList = [1, 1, 3, 3, 5, 5];

clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];
load (clustersPath);

imsizes = {};
for i = 1 : length(clusters)
    imsizes{i} = clusters(i).carsize;
end
assert (length(clusters) == length(posList));


%% work

for i = 1 : length(clusters)
    fprintf('Training model for cluster %d...\n', i);

    % patches dir
    patchesPosDir = [CITY_DATA_PATH sprintf('violajones/patches/pos-%02d/',posList(i))];
    patchesNegDir = [CITY_DATA_PATH sprintf('violajones/patches/neg-%02d/',negList(i))];

    imsize = imsizes{i};

    % output model path
    outModelPath = [CITY_DATA_PATH, sprintf('violajones/models/model-%02d.xml',i)];    
    
    trainCascade (patchesPosDir, patchesNegDir, outModelPath, imsize);
end
