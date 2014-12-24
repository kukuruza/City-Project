% Learn car appearance models from data

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;



%% input

verbose = 1;
dowrite = false;
dopause = 0.3;

videoPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.avi'];
timestampPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.txt'];


%% output

outPatchesDir = [CITY_DATA_PATH 'testdata/learning/cam572-sparse1/patches/'];
outCarsDir = [CITY_DATA_PATH 'testdata/learning/cam572-sparse1/cars/'];


%% init

% frame reader
frameReader = FrameReaderVideo (videoPath, timestampPath);

% background
%background = BackgroundGMM ('fn_level', 15, ...
%                            'fp_level', 1, ...
%                            'minimum_blob_area', 50);
load ([CITY_DATA_PATH, 'camdata/cam572/10am/models/backgroundGMM.mat']);

% true background
backImage = imread([CITY_DATA_PATH, 'camdata/cam572/10am/background1.png']);

% geometry
cameraId = 572;
image = imread([CITY_SRC_PATH 'geometry/cam572.png']);
matFile = [CITY_SRC_PATH 'geometry/' sprintf('Geometry_Camera_%d.mat', cameraId)];
geom = GeometryEstimator(image, matFile);

roadCameraMap = geom.getCameraRoadMap();
orientationMap = geom.getOrientationMap();


%% work

for t = 1 : 100000
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    gray = rgb2gray(frame);
    frame_out = frame;
    fprintf ('frame: %d\n', t);

    % get the trace of foreground. Cars will be learned from this.
    frameTrace = abs(backImage - frame);

    % subtract background and return mask
    foregroundMask = background.subtract(frame);
    
    cars = Car.empty;
    for k = 1 : size(bboxes,1)
        cars(k) = Car(bboxes(k,:));
    end
    foregroundMask = imerode (foregroundMask, strel('disk', 2));
    foregroundMask = imdilate(foregroundMask, strel('disk', 2));
    if verbose > 0
        figure(2)
        subplot(1,2,1), imshow(foregroundMask);
        subplot(1,2,2), imshow(frameTrace);
    end
    fprintf ('background cars: %d\n', length(cars));
    
    % assigning orientation
    for j = 1 : length(cars)
        center = cars(j).getBottomCenter();
        cars(j).orientation = [orientationMap.yaw(center(1), center(2)) ...
                               orientationMap.pitch(center(1), center(2))];
        cars(j).orientation
    end

    % filter: sizes (size is sqrt of area)
    SizeTolerance = 1.5;
    counter = 1;
    carsFilt = Car.empty;
    for j = 1 : length(cars)
        center = cars(j).getBottomCenter(); % [y x]
        expectedSize = roadCameraMap(center(1), center(2));
        actualSize = sqrt(single(cars(j).bbox(3) * cars(j).bbox(4)));
        if actualSize > expectedSize / SizeTolerance && ...
           actualSize < expectedSize * SizeTolerance
            carsFilt(counter) = cars(j);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    fprintf ('sized cars:      %d\n', length(cars));
    
    
    % filter: bbox proportion
    Heght2Width = [0.2 3];
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
    SafeDistance = 2.0;
    counter = 1;
    carsFilt = Car.empty;
    for j = 1 : length(cars)
        center = cars(j).getCenter(); % [y x]
        expectedSize = roadCameraMap(center(1), center(2));
        isOk = true;
        for k = 1 : length(cars)
            if dist(center, cars(k).getCenter()') < expectedSize * SafeDistance
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
        expectedSize = roadCameraMap(center(1), center(2));
        roi = cars(j).getROI();
        min([roi(1:2), size(frame,1)-roi(3), size(frame,2)-roi(2)])
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
        frame_out = cars(j).drawCar(frame_out, 'color', 'yellow', 'tag', 'detected');
        car = cars(j);
        car.patch = car.extractPatch(frameTrace); % cars are learned from trace
        namePrefix = ['f' sprintf('%03d',t) '-car' sprintf('%03d',j)];
        if dowrite
            save ([outCarsDir namePrefix '.mat'], 'car');
            imwrite(car.patch, [outPatchesDir namePrefix '.png']);
        end
    end
    if verbose > 0
        figure(1)
        imshow(frame_out);
        pause (max(0.1, dopause));
    end
end

clear frameReader



