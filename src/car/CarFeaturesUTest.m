% test for car features - how good features describe a car
%

% input
imDir = [CITY_DATA_PATH 'testdata/carcuont/'];
imageNames = ...
{'1a-cam671-0004.png', ...
 '1b-cam671-0003.png', ...
 '1c-cam671-0005.png', ...
 '1n-cam671-0003.png', ...
 '1m-cam671-0005.png', ...
};

% ground truth
% ims{1} == ims{2}, ims{1} == ims{3},
% ims{1} != ims{4}, ims{1} != ims{5}

for i = 1 : length(imageNames)
    ims{i} = imread(fullfile(imDir, imageNames{1}));
end


