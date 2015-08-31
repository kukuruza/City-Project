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
%db_path = [CITY_DATA_PATH 'datasets/labelme/Databases/572-Oct30-17h-fr/Apr01-masks-ex0.1-di0.3-er0.3.db'];
db_path = [CITY_DATA_PATH, 'datasets/labelme/Databases/572-Nov28-10h-pair/detected/all-1.db'];
%% show all information about every car in every image

% open database
sqlite3.open (db_path);

% read imagefiles
imagefiles = sqlite3.execute('SELECT imagefile,time FROM images');

for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    img = imread(fullfile(CITY_DATA_PATH, imagefile));
    
    % we store time in different formats in Car and in .db for now
    timestamp = db2matlabTime(imagefiles(i).time);
    
    % get all info about cars for this match
    car_entries = sqlite3.execute('SELECT * FROM cars WHERE imagefile = ?', imagefile);

    % parse the result and draw the car on the image
    for car_entry = [car_entries]
        
        % create and show Car object
        bbox = [car_entry.x1, car_entry.y1, car_entry.width, car_entry.height];
        car = Car (bbox, timestamp, car_entry.name);
        img = car.drawCar (img);
    end
    
    imshow(img)

   waitforbuttonpress
end

sqlite3.close();


