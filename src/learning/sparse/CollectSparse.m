% Collect patches seen by background detector
% Takes a original video, as well as ghost video on input
%   If background detector sees a very distinct spot, it becomes a car
%   Patch, ghost, orientation, size of the car is extracted
%
% Note: reason for using ghost video as opposed to ghost image
%       is the possibility to use varying illumination conditions
%       They are encoded in the video, but not the image.

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

% for sparse dataset need strict parameters
DensitySigma = 2.5;   % effective radius around car to be empty
DensityRatio = 12.0;   % how much dense inside / sparse outside it should be

filter_by_sparsity = false;
write_db = true;
verbose = 0;

videoName = 'camdata/cam541/Jul26-16h';
videoPath = [CITY_DATA_PATH videoName '.avi'];
ghostPath = [CITY_DATA_PATH videoName '-ghost.avi'];
timePath = [CITY_DATA_PATH videoName '.txt'];


%% output

dir_name = '541-Jul26-16h';
db_name = 'src.db';


%% init

dataset_dir = 'datasets/unlabelled/';
if ~exist ([CITY_DATA_PATH dataset_dir], 'dir')
    error ('dataset_dir doesn''t exist');
end

db_dir = [CITY_DATA_PATH dataset_dir 'Databases/' dir_name];
im_dir = [CITY_DATA_PATH dataset_dir 'Images/' dir_name];
gh_dir = [CITY_DATA_PATH dataset_dir 'Ghosts/' dir_name];
ma_dir = [CITY_DATA_PATH dataset_dir 'Masks/' dir_name];
if exist(db_dir, 'dir'), rmdir(db_dir, 's'); end; mkdir(db_dir);
if exist(im_dir, 'dir'), rmdir(im_dir, 's'); end; mkdir(im_dir);
if exist(gh_dir, 'dir'), rmdir(gh_dir, 's'); end; mkdir(gh_dir);
if exist(ma_dir, 'dir'), rmdir(ma_dir, 's'); end; mkdir(ma_dir);
dir_name = [dir_name '/'];


% frame reader
frameReader = FrameReaderVideo (videoPath, timePath);
ghostReader = FrameReaderImages (ghostPath, timePath);

% background
background = BackgroundGMM();

% out database
if write_db
    dbCreate([db_dir '/' db_name]);
    sqlite3.open([db_dir '/' db_name]);
end

%% work

for t = 1 : 10000000
    
    % read image
    [frame, timestamp] = frameReader.getNewFrame();
    [ghost, ~] = ghostReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % subtract background and return mask
    mask = background.subtract(frame);
    bboxes = background.mask2bboxes(mask);
    
    cars = Car.empty;
    for k = 1 : size(bboxes,1)
        cars(k) = Car(bboxes(k,:));
    end
    fprintf ('background cars: %d\n', length(cars));
    
    if write_db
        im_name = sprintf ('%06d', t-1);
        image_file = [dataset_dir 'Images/' dir_name im_name '.jpg'];
        ghost_file = [dataset_dir 'Ghosts/' dir_name im_name '.jpg'];
        mask_file =  [dataset_dir 'Masks/'  dir_name im_name '.png'];
        imwrite (frame, [CITY_DATA_PATH image_file]);
        imwrite (ghost, [CITY_DATA_PATH ghost_file]);
        imwrite (mask,  [CITY_DATA_PATH mask_file]);
    end
        
    statuses = cell(length(cars),1);
    for i = 1 : length(cars)
        statuses{i} = 'ok';
    end
    if filter_by_sparsity
        statuses = filterBySparsity (mask, cars, statuses, 'verbose', verbose, ...
                         'DensitySigma', DensitySigma, 'DensityRatio', DensityRatio);
        indices = find(cellfun('isempty', strfind(statuses, 'ok')));
        cars (indices) = [];
        fprintf ('sparse cars:     %d\n', length(cars));
    end
    
    % TODO: write scores to db

    if ~isempty(cars) && write_db
        width  = size(frame, 2);
        height = size(frame, 1);
        time_db = matlab2dbTime(timestamp);
        query = 'INSERT INTO images (imagefile,src,width,height,ghostfile,maskfile,time) VALUES (?,?,?,?,?,?,?)';
        sqlite3.execute(query, image_file, videoName, width, height, ghost_file, mask_file, time_db);
        for i = 1 : length(cars)
            car = cars(i);
            bbox = car.bbox;
            query = 'INSERT INTO cars(imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?)';
            sqlite3.execute(query, image_file, 'object', bbox(1), bbox(2), bbox(3), bbox(4));
        end
    end
    
    if verbose > 0
        frame_out = frame;
        mask_out  = uint8(mask(:,:,[1,1,1])) * 255;
        for j = 1 : length(cars)
            mask_out    = cars(j).drawCar(mask_out, 'color', 'yellow', 'tag', 'detected');
            frame_out   = cars(j).drawCar(frame_out, 'color', 'yellow', 'tag', 'detected');
        end
        figure (1)
        subplot(2,2,1), imshow(mask_out);
        subplot(2,2,2), imshow(ghost);
        subplot(2,2,3), imshow(frame_out);
        pause()
    end
end

clear frameReader
clear ghostReader
if write_db
    sqlite3.close();
end



