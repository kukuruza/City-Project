% Train a cascade for each cluster
% 


clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';



%% input

iclusters = [3];

clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];
load (clustersPath);


%% work

for i = iclusters
    fprintf('Training model for cluster %d\n', i);

    % patches dir
    patchesPosDir = [CITY_DATA_PATH sprintf('violajones/patches/pos-%02d/',i)];
    patchesNegDir = [CITY_DATA_PATH 'violajones/patches/neg/'];

    imsize = clusters(i).carsize;

    % output model path
    outModelPath = [CITY_DATA_PATH, sprintf('violajones/models/model-%02d-cr10.xml',i)];    
    
    trainCascade (patchesPosDir, patchesNegDir, outModelPath, imsize, 'crop', 0.1);
end
