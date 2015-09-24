%
% example of reading cars db from matlab
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input
db_path = [CITY_DATA_PATH, 'databases/labelme/572-Nov28-10h-pair/parsed-ghost.db'];
assert (exist(db_path, 'file') == 2);

%% show all information about every car in every image

% tool to read images straight from video
imgReader = ImgReaderVideo();

% open database
sqlite3.open (db_path);

% read imagefiles
image_entries = sqlite3.execute('SELECT imagefile,time FROM images');
for image_entry = [image_entries]
    img = imgReader.imread(image_entry.imagefile);
    
    % get all info about cars for this match
    car_entries = sqlite3.execute('SELECT * FROM cars WHERE imagefile = ?', image_entry.imagefile);

    % parse the result and draw the car on the image
    for car_entry = [car_entries]
        
        % create and show Car object
        bbox = [car_entry.x1, car_entry.y1, car_entry.width, car_entry.height];
        car = Car ('bbox', bbox, 'timestamp', image_entry.time, 'name', car_entry.name);
        img = car.drawCar (img);
    end
    
    imshow(img)
    waitforbuttonpress
    
end
sqlite3.close();


