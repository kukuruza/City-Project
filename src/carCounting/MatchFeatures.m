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
db_path = fullfile(CITY_DATA_PATH, 'datasets/labelme/Databases/572-Oct30-17h-pair/parsed-image.db');
sqlite3.open (db_path);


%% input features
features_path = fullfile(CITY_DATA_PATH, 'cnn/features/572-Oct30-17h-pair-ip1.txt');

ids_and_features = importdata(features_path);
featureID = ids_and_features.textdata;
features  = ids_and_features.data;
fprintf ('have read %d features, each of length %d.\n', size(features));
count = length(featureID);

featureids = zeros(count,1);
for i = 1:count
 s1 = featureID(i);
 s2 = strrep(s1,'.png','');
 featureids(i,1) = str2num(cell2mat(s2));
end


%% get all positives

% get all matches
matches = sqlite3.execute('SELECT DISTINCT match FROM matches');

counter_pos = 0;
for match = [matches.match];
    
    % get cars for this match
    query = 'SELECT carid FROM matches WHERE match = ?';
    carids = sqlite3.execute(query, match);
    %fprintf ('match %d: found %d cars.\n', match, length(carids));
    
    % concatenate two feature for each pair
    %   car1 <-> car1 is a positive pair
    %   car1 <-> car2 and car2 <-> car1 are different pairs
    for carid1 = [carids.carid]
        for carid2 = [carids.carid]

            % find carid1 and carid2 in the features
            feature1 = features (featureids == carid1, :);
            feature2 = features (featureids == carid2, :);
            % not all the cars get a feature, there are filters on size, type, etc
            if isempty(feature1) || isempty(feature2), continue, end
            % there can be only one feature with this index
            assert (isvector(feature1) && isvector(feature2));
            
            % a single positive sample
            positive = [feature1 feature2];
            counter_pos = counter_pos + 1;
            PosCase(counter_pos,:) = positive;
        end
    end
end
save('PosCase.mat', 'PosCase');
fprintf ('found %d positive samples\n', counter_pos);
 

%% get some negatives

% required number of negatives
numNegatives = 4000;

% find the number of all cars
numcars = length(featureids);
fprintf ('number of all cars in db: %d \n', numcars);

% generate many random non-repeating pairs of ids (that may or may not match)
randomPairs = randperm (numcars^2, numNegatives * 10);
randomPairs = [floor(randomPairs / numcars); mod(randomPairs, numcars)] + 1;

% do until have enough
counter_neg = 0;
for i = 1 : size(randomPairs,2)
    
    % get the id of the first and the second cars
    randomPair = randomPairs(:,i);
    carid1 = featureids (randomPair(1));
    carid2 = featureids (randomPair(2));
    
    % make sure both cars are in the table
    found_car1 = sqlite3.execute('SELECT COUNT(*) FROM cars WHERE id = ?', carid1);
    found_car2 = sqlite3.execute('SELECT COUNT(*) FROM cars WHERE id = ?', carid2);
    assert (found_car1.count && found_car2.count);
    
    % if there is a match between two cars, skip this pair and continue
    query = ['SELECT COUNT(*) FROM matches WHERE match IN ' ...
             '(SELECT match FROM matches WHERE carid = ? INTERSECT ' ...
             'SELECT match FROM matches WHERE carid = ?)'];
    found_match = sqlite3.execute(query, carid1, carid2);
    if found_match.count, continue, end
    
    feature1 = features (randomPair(1),:);
    feature2 = features (randomPair(2),:);
    
    % a single negative sample
    negative = [feature1 feature2];
            
    % condition to exit the loop
    if counter_neg == numNegatives, break, end
    
    counter_neg = counter_neg + 1;
    NegCase(counter_neg,:) = negative;
end
save('NegCase.mat', 'NegCase');
fprintf ('found %d negative samples\n', counter_neg);


sqlite3.close();


