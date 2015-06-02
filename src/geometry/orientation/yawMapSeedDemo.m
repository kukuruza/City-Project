% Script to test the prediction of yaw maps using CNNs
% We begin with a crude three way classification into:
% (a) 0 = [0, 22.5] (b) 45 = [22.5, 67.5], (d) 90 = [67.5, 90]
%
% The orientations for observed cars are marked and smoothed to get the
% first estimate of the map
% Camera: 717 
% Database: datasets/sparse/databases/717-Apr07-15h/color-e0.1.db

%% Setting up the paths from the environmental variables
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

%% Reading the txt file
anglePath = fullfile(CITY_DATA_PATH, 'models/cam717/predicted_angles.txt');
fileId = fopen(anglePath, 'r');
angleData = textscan(fileId, '%s %d\n');
% Separating the car ids and predicted angles
imgPaths = angleData{1};
angles = angleData{2};

%% Fetching the corresponding bounding box from database
dbPath = fullfile(CITY_DATA_PATH, 'datasets/sparse/databases/717-Apr07-15h/color.db');
sqlite3.open (dbPath);
sqlCommand = 'SELECT x1, y1, width, height FROM cars WHERE id = ?';

%% Reading a frame for debugging
framePath = fullfile(CITY_DATA_PATH, 'camdata/cam717/Apr07-15h.jpg');
frame = imread(framePath);

% Initialize the empty map (camera 717 is 352 x 240)
yawMap = zeros(size(frame, 1), size(frame, 2)) - 45;

%% For each entry, populate the position of the car
for i = 1:numel(imgPaths)
    carId = textscan(imgPaths{i}, '%d.png');
    carInfo = sqlite3.execute(sqlCommand, carId{1});
    
    % Taking 25% above bottom center as location of car
    carCenter = uint32([carInfo.x1 + carInfo.width/2, carInfo.y1 + 3/4 * carInfo.height]);
    yawMap(carCenter(2), carCenter(1)) = angles(i);
end

mask = 255 * uint8(yawMap > -45);

%% Smoothing the yaw map using soap film

% yawMap = roadSoapFilm (yawMap, 255 - mask, ...
%                        'thresh', 0.01, ...
%                        'sizeContour', 20, ...
%                        'sizeBody', 10, ...
%                        'verbose', 1);

figure(1); imagesc(yawMap)
figure(2); imshow(frame)