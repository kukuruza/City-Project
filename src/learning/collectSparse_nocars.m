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

verbose = 0;
dopause = 0.3;

videoName = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours'];
videoPath = [videoName '.avi'];
timePath = [videoName '.txt'];


%% output
dir_name = 'datasets/sparse/572-10h';
outDir = [CITY_DATA_PATH dir_name];
db_name = 'sparse-1.db';
if ~exist (fileparts(outDir), 'dir')
    error ('parent directory for outDir doesn''t exist');
end
if exist(outDir, 'dir')
    rmdir(outDir, 's');
end
dir_name = [dir_name '/'];
outDir = [outDir '/'];
mkdir(outDir);
mkdir([outDir 'Images/']);
mkdir([outDir 'Ghosts/']);
mkdir([outDir 'Masks/']);
mkdir([outDir 'Databases/']);

%% init

% frame reader
frameReader = FrameReaderVideo (videoPath, timePath);

% background
load ([CITY_DATA_PATH, 'models/cam572/backgroundGMM.mat']);
%pretrainBackground (background, [CITY_DATA_PATH 'camdata/cam572/5pm/']);

% true background
backImage = int32(imread([CITY_DATA_PATH, 'camdata/cam572/10am/background1.png']));

% geometry
load([CITY_DATA_PATH 'models/cam572/GeometryObject_Camera_572.mat']);
sizeMap = geom.getCameraRoadMap();
orientationMap = geom.getOrientationMap();

% out database
db_path = [outDir 'Databases/' db_name];
createMaskDb(db_path);
sqlite3.open(db_path);


%% work

for t = 1 : 10
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % get the trace of foreground. Cars will be learned from this.
    frame_ghost = uint8((int32(frame) - int32(backImage)) / 2 + 128);

    % subtract background and return mask
    mask = background.subtract(frame);
    bboxes = background.mask2bboxes(mask);
    N = size(bboxes,1);
    
%     mask = imerode (mask, strel('disk', 2));
%     mask = imdilate(mask, strel('disk', 2));
    fprintf ('background cars: %d\n', length(cars));
    
    im_name = sprintf ('%06d', t);
    image_file = [dir_name 'Images/' im_name '.jpg'];
    ghost_file = [dir_name 'Ghosts/' im_name '.jpg'];
    mask_file = [dir_name 'Masks/'  im_name '.png'];
    imwrite (frame, [CITY_DATA_PATH image_file]);
    imwrite (frame_ghost, [CITY_DATA_PATH ghost_file]);
    imwrite (mask, [CITY_DATA_PATH mask_file]);
        
    % filter sparse in the image
    SafeDistance = 0.0;
    areBad = [];
    for j = 1 : N
        centers = [int32(bboxes(:,2) + 0.5 * bboxes(:,4)), ...
                   int32(bboxes(:,1) + 0.5 * bboxes(:,3))];
    end
    for j = 1 : N
        center = centers(i,:);
        expectedSize = sizeMap(center(1), center(2));
        for k = 1 : N
            % TODO: replace dist from Neural Network toolbox
            if j ~= k && dist(center, center(k,:)') < expectedSize * SafeDistance
               areBad = [areBad, j];
            end
        end
    end
    bboxes (areBad, :) = [];
    fprintf ('sparse cars:     %d\n', size(bboxes,1));
    N = size(bboxes,1);
    
    frame_out = frame;
    mask_out = zeros(size(frame));

    if N > 0
        width  = size(frame, 2);
        height = size(frame, 1);
        sqlite3.execute('INSERT INTO images VALUES (?,?,?,?)', ...
                        image_file, videoName, width, height);
        sqlite3.execute('INSERT INTO masks VALUES (?)', mask_file);
        for i = 1 : N
            bbox = cars.bbox;
            sqlite3.execute(['INSERT INTO cars(imagefile, name, x1, y1, width, height, ' ...
                             'offsetx, offsety) VALUES (?,?,?,?,?,?,?,?) '], ...
                             image_file, 'vehicle', bbox(1), bbox(2), bbox(3), bbox(4), 0, 0);
        end
    end
    
    for j = 1 : length(cars)
        mask_out    = cars(j).drawCar(mask_out, 'color', 'yellow', 'tag', 'detected');
        frame_out   = cars(j).drawCar(frame_out, 'color', 'yellow', 'tag', 'detected');
    end
    if verbose > 0
        figure(1)
        subplot(2,2,1), imshow(mask_out);
        subplot(2,2,2), imshow(frame_ghost);
        subplot(2,2,3), imshow(frame_out);
        pause (max(0.1, dopause));
    end
end

clear frameReader



