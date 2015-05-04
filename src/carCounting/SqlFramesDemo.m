%
% example of reading cars db from matlab
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
run ([getenv('CITY_PATH') 'src/subdirPathsSetup.m']);  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input
db_path = [CITY_DATA_PATH 'datasets/labelme/Databases/572-Oct30-17h-pair/parsed.db'];



%% show all information about every car in every image

% open database
sqlite3.open (db_path);

% read imagefiles
imagefiles = sqlite3.execute('SELECT imagefile,time FROM images');

for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    img = imread([CITY_DATA_PATH imagefile]);
    
    % we store time in different formats in Car and in .db for now
    timestamp = db2matlabTime(imagefiles(i).time);
    
    % get all info about cars for this match
    query = 'SELECT * FROM cars WHERE imagefile = ?';
    car_entries = sqlite3.execute(query, imagefile);

    % parse the result and draw the car on the image
    for j = 1 : length(car_entries)
        car_entry = car_entries(j);
        
        % create and show Car object
        bbox = [car_entry.x1, car_entry.y1, car_entry.width, car_entry.height];
        car = Car (bbox, timestamp, car_entry.name);
        img = car.drawCar (img);
    end
    
    imshow(img)
    waitforbuttonpress
end

sqlite3.close();


