%
% example of reading all matching cars from dababase to matlab
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
run ([getenv('CITY_PATH') 'src/subdirPathsSetup.m']);  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input
db_path = [CITY_DATA_PATH 'datasets/labelme/Databases/572-Oct30-17h-pair/parsed.db'];



%% show all information about every match in every image

% open database
sqlite3.open (db_path);

% read imagefiles, each of them is a pair of images
imagefiles = sqlite3.execute('SELECT imagefile FROM images');

for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    
    % get (distinct) matches for this pairfile
    query = 'SELECT DISTINCT match FROM matches WHERE carid IN (SELECT id FROM cars WHERE imagefile = ?)';
    matches = sqlite3.execute(query, imagefile);
    fprintf ('%s: found %d matches.\n', imagefile, length(matches));
    
    for match = [matches.match]

        % find all cars, including from different frames, that do match
        carids = sqlite3.execute('SELECT carid FROM matches WHERE match = ?', match);
        fprintf ('  match #%d: found %d cars:\n', match, length(carids));
        
        for carid = [carids.carid]
            
            % get all information about a car
            car_entry = sqlite3.execute('SELECT * FROM cars WHERE id = ?', carid);
            bbox = [car_entry.x1, car_entry.y1, car_entry.width, car_entry.height];
            fprintf ('    #%04d: bbox=[%d %d %d %d] in image: %s\n', ...
                car_entry.id, bbox, car_entry.imagefile);

            % load that match from every image
            img = imread([CITY_DATA_PATH car_entry.imagefile]);
            img = insertObjectAnnotation(img, 'rectangle', bbox, car_entry.name);
            imshow(img)
            waitforbuttonpress

        end
    end
end

sqlite3.close();


