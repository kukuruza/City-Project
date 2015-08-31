%
% compile positive and negative samples from features
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input db
db_path = fullfile(CITY_DATA_PATH, 'datasets/labelme/Databases/572-Oct30-17h-pair/parsed.db');
sqlite3.open (db_path);


%% input features
features_path = fullfile(CITY_DATA_PATH, 'cnn/features/572-Oct30-17h-pair-ip1.txt');

ids_and_features = importdata(features_path);
featureids = ids_and_features.textdata;
features  = ids_and_features.data;
% featureids = ids_and_features(:,1);     % the first column is car ids
% features  = ids_and_features(:,2:end);  % the rest is the features
fprintf ('have read %d features, each of length %d.\n', size(features));