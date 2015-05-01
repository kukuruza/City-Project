%
% example of reading cars db from matlab
%


clear all
% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));
% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


%% input

db_path = [CITY_DATA_PATH 'datasets/labelme/Databases/572/distinct-frames.db'];



%% work

% open database
sqlite3.open (db_path);

% read imagefiles
imagefiles = sqlite3.execute('SELECT imagefile FROM images');

for i = 1 : length(imagefiles)
    % get the field 'imagefile' from i-th element of the structures
    imagefile = imagefiles(i).imagefile;
    image = imread([CITY_DATA_PATH imagefile]);
    
    % get all info about two (or one if no match) cars for this match
    query = 'SELECT * FROM cars WHERE imagefile = ?';
    car_entries = sqlite3.execute(query, imagefile);

    % parse the result and draw the car on the image
    for j = 1 : length(car_entries)
        car_entry = car_entries(j);
        bbox = [car_entry.x1, car_entry.y1, car_entry.width, car_entry.height];
        car = Car ('timestamp', [0 0 0 0 0 0], 'bbox', bbox);
        image = car.drawCar (image);
    end
    
    imshow(image)
    waitforbuttonpress();
end

sqlite3.close();


