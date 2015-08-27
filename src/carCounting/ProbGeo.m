%
% example of reading cars db from matlab
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%geom = GeometryEstimator(frame, matFile);
% Loading the road properties that were manually marked (Pts for the lanes)
% Geometry object can be simply loaded using the object file
% The object geom will be directly loaded. However, newer functionalities
% might need this object to be created again
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf(strcat('Read Geometry object from file, might not be the latest version\n' , ...
    'Update if made changes to GeometryEstimator class\n'));
counting = MetricLearner(geom); % pass necessary arguments to constructor
count0 = 0; % initial should be the number of cars in the first frame


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
























inCarsDir = [CITY_DATA_PATH 'labelme/Cars/cam572-5pm-pairs/'];  % must have "/" in the end

for t = 1 : 99
    carsList = dir([inCarsDir sprintf('%03d', t) '-' sprintf('%03d', t+1) '-*.mat']);

    for i = 1 : length(carsList)

        % load car object
        clear car
        load ([inCarsDir carsList(i).name]);

        % generate features
        if ~isempty(cars(1,1).bbox)&& ~isempty(cars(1,2).bbox)
            % match
            P1 = cars(1,1).patch;
            P2 = cars(1,2).patch;
            cars(1,1).gFeature(P1);
            cars(1,2).gFeature(P2);
            % HOG
            dHOG = chi_square_statistics(cars(1,1).histHog,cars(1,2).histHog);
            % ProbHOG = 1-dHOG;          
            % Color           
            dCol = chi_square_statistics(cars(1,1).histCol,cars(1,2).histCol);
            % ProbCol = 1-4*dCol;
            % ProbGeo = counting.geometryObj.generateProbMatrix(cars(1,1), cars(1,2));
            DistH(t,i) = dHOG;
            DistC(t,i) = dCol;
            % ProbG(t,i) = ProbGeo;
        end
    end
end
save('ProbG.mat','ProbG');