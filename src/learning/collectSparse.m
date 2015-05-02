% Learn car appearance models from data
%   If background detector sees a very distinct spot, it becomes a car
%   Patch, ghost, orientation, size of the car is extracted

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;



%% input

DensitySigma = 2.5;   % effective radius around car to be empty
DensityRatio = 12.0;   % how much dense inside / sparse outside it should be

do_write = true;
verbose = 0;

videoName = 'camdata/cam671/Mar24-12h';
videoPath = [CITY_DATA_PATH videoName '.avi'];
timePath = [CITY_DATA_PATH videoName '.txt'];

backfile = 'camdata/cam671/models/backimage.png';


%% output

dir_name = '671-Mar24-12h';
db_name = 'src-ds2.5-dp12.0.db';


%% init

dataset_dir = 'datasets/sparse/';
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
%frameReader = FrameReaderImages (imagesPath);

% background
load ([CITY_DATA_PATH, 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);

% true background
backImage = int32(imread([CITY_DATA_PATH, backfile]));

% out database
if do_write
    dbCreate([db_dir '/' db_name]);
    sqlite3.open([db_dir '/' db_name]);
end


%% work

for t = 1 : 10000000
    
    % read image
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % get the trace of foreground. Cars will be learned from this.
    ghost = uint8((int32(frame) - int32(backImage)) / 2 + 128);

    % subtract background and return mask
    mask = background.subtract(frame);
    bboxes = background.mask2bboxes(mask);
    
    cars = Car.empty;
    for k = 1 : size(bboxes,1)
        cars(k) = Car(bboxes(k,:));
    end
    fprintf ('background cars: %d\n', length(cars));
    
    if do_write
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
    statuses = filterBySparsity (mask, cars, statuses, 'verbose', verbose, ...
                     'DensitySigma', DensitySigma, 'DensityRatio', DensityRatio);
    indices = find(cellfun('isempty', strfind(statuses, 'ok')));
    cars (indices) = [];
    fprintf ('sparse cars:     %d\n', length(cars));

    if ~isempty(cars) && do_write
        width  = size(frame, 2);
        height = size(frame, 1);
        time_py = matlab2pyTime(timestamp);
        query = 'INSERT INTO images VALUES (imagefile,src,width,height,ghostfile,maskfile,time)';
        sqlite3.execute(query, image_file, videoName, width, height, ghost_file, mask_file, time_py);
        for i = 1 : length(cars)
            car = cars(i);
            bbox = car.bbox;
            query = ['INSERT INTO cars(imagefile,name,x1,y1,width,height,offsetx, offsety) ' ...
                     'VALUES (?,?,?,?,?,?,?,?)'];
            sqlite3.execute(query, image_file, 'object', bbox(1), bbox(2), bbox(3), bbox(4), 0, 0);
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
if do_write
    sqlite3.close();
end



