% read Car objects, display them, and extract color from them

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



% input
groundTruthPath = 'testdata/carcolor/groundTruth.txt';
imagesDir = fileparts(groundTruthPath);

% read ground truth, which elso has the names of files
lines = readList(groundTruthPath);

for i = 1 : length(lines)
    line = char(lines(i));
    
    % split into words
    space = find(line == ' ');
    assert (isscalar(space));
    assert (space < length(line));
    name = line(1:space-1);
    trueColorName = line(space+1:end)
    
    % test the function to find the color
    clear car;
    carPath = [imagesDir '/' name '.mat'];
    load (carPath);
    
    estimatedColor = carColor(car)
    
    % display image
    imshow(car.patch);
    pause
end
    
    
    