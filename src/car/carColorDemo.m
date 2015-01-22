% read Car objects, display them, and extract color from them

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../rootPathsSetup.m';
run '../subdirPathsSetup.m'



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
    
    
    