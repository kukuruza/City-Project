% read matches database and write pairs of cars that satisfy filters
% 
% The Sqlite3 interface uses 'matlab-sqlite3-driver'
%   (https://github.com/kyamagu/matlab-sqlite3-driver)
%   This package must be installed already
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;

labelme_path = [CITY_DATA_PATH 'labelme/'];
db_path = [CITY_DATA_PATH 'labelme/Databases/all-wratio.db'];
backimage_path = [CITY_DATA_PATH 'camdata/cam572/5pm/models/backimage.png'];
out_dir = [CITY_DATA_PATH 'labelme/Cars/all-wratio/'];

backimage = imread(backimage_path);
backimage = [backimage; backimage];  % two rows

if ~exist(out_dir, 'dir')
    mkdir(out_dir)
end

% no filters now


sqlite3.open(db_path);

% find different matches entries
matches = sqlite3.execute('SELECT DISTINCT match FROM matches');

for i = 1 : length(matches)
    % find cars for every match
    match = matches(i).match;
    query_str = sprintf('SELECT carid FROM matches WHERE match = %d', match);
    carids = sqlite3.execute (query_str);
    assert (~isempty(carids));
    
    cars = Car.empty();
    for j = 1 : length(carids)
        carid = carids(j).carid;
        
        car = Car();

        if carid ~= 0
            % get the car
            query_str = sprintf('SELECT * FROM cars WHERE id = %d', carid);
            entry = sqlite3.execute (query_str);
            assert (length(entry) == 1);

            % read file
            impath = [labelme_path 'Images/' entry.imagefile];
            if ~exist(impath, 'file')
                error ('file doesn''t exist: "%s"', impath);
            end
            im = imread(impath);

            ghost = uint8(int32(im) - int32(backimage) + 128);

            roi = 1 + [entry.y1 + entry.offsety, ...
                       entry.x1 + entry.offsetx, ...
                       entry.y1 + entry.offsety + entry.height - 1, ...
                       entry.x1 + entry.offsetx + entry.width - 1];
            patch = im (roi(1):roi(3), roi(2):roi(4), :);
            ghost_patch = ghost (roi(1):roi(3), roi(2):roi(4), :);
            imshow ([patch, ghost_patch])
            pause (0.2)

            roi = [entry.y1, entry.x1, entry.y1+entry.height-1, entry.x1+entry.width-1] + 1;
            car.bbox = roi2bbox(roi);
            car.name = entry.name;
            car.patch = patch;
            car.ghost = ghost_patch;
            car.orientation = [entry.yaw, entry.pitch];
        end
        
        cars = [cars, car];
        [~, framepair, ~] = fileparts (entry.imagefile);
        save ([out_dir sprintf('%s-%06d.mat', framepair, match)], 'cars');
    end
    
end
