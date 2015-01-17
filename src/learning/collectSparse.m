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
dowrite = true;
dowriteFrames = true;
dopause = 0.3;

videoPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.avi'];
timestampPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.txt'];


%% output
outDir = [CITY_DATA_PATH 'learning/cam572-sparse3/'];

if exist(outDir, 'dir')
    rmdir(outDir, 's');
end
mkdir(outDir);
mkdir([outDir 'cars/']);
mkdir([outDir 'frames/']);
mkdir([outDir 'ghosts/']);
mkdir([outDir 'patches/']);


%% init

% frame reader
frameReader = FrameReaderVideo (videoPath, timestampPath);

% background
load ([CITY_DATA_PATH, 'camdata/cam572/10am/models/backgroundGMM.mat']);

% true background
backImage = int32(imread([CITY_DATA_PATH, 'camdata/cam572/10am/background1.png']));

% geometry
load('GeometryObject_Camera_572.mat');
sizeMap = geom.getCameraRoadMap();
orientationMap = geom.getOrientationMap();


%% work

for t = 1 : 100000
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    frame_out = frame;
    fprintf ('frame: %d\n', t);

    % get the trace of foreground. Cars will be learned from this.
    frame_ghost = uint8((int32(frame) - int32(backImage)) / 2 + 128);

    % subtract background and return mask
    mask = background.subtract(frame);
    bboxes = background.mask2bboxes(mask);
    
    cars = Car.empty;
    for k = 1 : size(bboxes,1)
        cars(k) = Car(bboxes(k,:));
    end
%     mask = imerode (mask, strel('disk', 2));
%     mask = imdilate(mask, strel('disk', 2));
    fprintf ('background cars: %d\n', length(cars));
    
    % assigning orientation
    for j = 1 : length(cars)
        center = cars(j).getBottomCenter();
        cars(j).orientation = [orientationMap.yaw(center(1), center(2)) ...
                               orientationMap.pitch(center(1), center(2))];
    end

    % filter: sizes (size is sqrt of area)
    SizeTolerance = 1.5;
    counter = 1;
    carsFilt = Car.empty;
    for j = 1 : length(cars)
        center = cars(j).getBottomCenter(); % [y x]
        expectedSize = sizeMap(center(1), center(2));
        actualSize = sqrt(single(cars(j).bbox(3) * cars(j).bbox(4)));
        if actualSize > expectedSize / SizeTolerance && ...
           actualSize < expectedSize * SizeTolerance
            carsFilt(counter) = cars(j);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    fprintf ('sized cars:      %d\n', length(cars));

    mask_out = cat(3, uint8(mask), uint8(mask), uint8(mask)) * 255;
    for j = 1 : length(cars)
        mask_out = cars(j).drawCar(mask_out, 'color', 'blue', 'tag', 'sized');
    end
    
    % filter: bbox proportion
    Heght2Width = [0.5 1.2];
    counter = 1;
    carsFilt = Car.empty;
    for j = 1 : length(cars)
        proportion = cars(j).bbox(4) / double(cars(j).bbox(3));
        if proportion > Heght2Width(1) && proportion < Heght2Width(2)
            carsFilt(counter) = cars(j);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    fprintf ('square cars:     %d\n', length(cars));
    
    
    % filter: sparse in the image
    SafeDistance = 0.0;
    counter = 1;
    carsFilt = Car.empty;
    for j = 1 : length(cars)
        center = cars(j).getCenter(); % [y x]
        expectedSize = sizeMap(center(1), center(2));
        isOk = true;
        for k = 1 : length(cars)
            if j ~= k && dist(center, cars(k).getCenter()') < expectedSize * SafeDistance
                isOk = false;
            end
        end
        if isOk
            carsFilt(counter) = cars(j);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    fprintf ('sparse cars:     %d\n', length(cars));
    for j = 1 : length(cars)
        frame_out = cars(j).drawCar(frame_out, 'color', 'blue', 'tag', 'sparse');
    end
    
    
    % filter: close to the border
    DistToBorder = 20;  % need at least DistToBorder pixels to border
    counter = 1;
    carsFilt = Car.empty;
    for j = 1 : length(cars)
        center = cars(j).getCenter(); % [y x]
        expectedSize = sizeMap(center(1), center(2));
        roi = cars(j).getROI();
        %min([roi(1:2), size(frame,1)-roi(3), size(frame,2)-roi(2)])
        if min([roi(1:2), size(frame,1)-roi(3), size(frame,2)-roi(4)]) > DistToBorder
            carsFilt(counter) = cars(j);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    fprintf ('non-border cars: %d\n', length(cars));
    
    
    % expand boxes
    ExpandPerc = 0.15;
    for j = 1 : length(cars)
        cars(j).bbox = expandBboxes (cars(j).bbox, ExpandPerc, frame);
    end

    
    % output
    frame_out = frame;

    for j = 1 : length(cars)
        car = cars(j);
        car.segmentMask = car.extractPatch(mask);
        car.ghost = car.extractPatch(frame_ghost);
        car.extractPatch(frame);
        namePrefix = ['f' sprintf('%03d',t) '-car' sprintf('%03d',j)];
        if dowrite
            save ([outDir 'cars/' namePrefix '.mat'], 'car');
            imwrite(car.patch, [outDir 'patches/' namePrefix '.png']);
            imwrite(uint8(abs(car.ghost)), [outDir 'ghosts/' namePrefix '.png']);
        end
    end
    
    for j = 1 : length(cars)
        mask_out    = cars(j).drawCar(mask_out, 'color', 'yellow', 'tag', 'detected');
        frame_out   = cars(j).drawCar(frame_out, 'color', 'yellow', 'tag', 'detected');
    end
    if dowriteFrames
        imwrite(frame,       [outDir 'frames/' sprintf('%03d',t) '-frame.jpg']);
        imwrite(frame_out,   [outDir 'frames/' sprintf('%03d',t) '-out.jpg']);
        imwrite(frame_ghost, [outDir 'frames/' sprintf('%03d',t) '-ghosts.jpg']);
        imwrite(mask_out,    [outDir 'frames/' sprintf('%03d',t) '-mask.jpg']);
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



