% Learn car appearance models from data

clear all


% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;



%% input

videoPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.avi'];
timestampPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.txt'];
%outImagePath = [CITY_DATA_PATH 'testdata/background/result/'];


%% init

% frame reader
frameReader = FrameReaderVideo (videoPath, timestampPath);

% background
background = Background();

% geometry
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf ('Have read the Geometry object from file\n');
roadCameraMap = geom.getCameraRoadMap();


t = 1;
while 1
    
    if t == 100, break, end
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    gray = rgb2gray(frame);
    
    % subtract background and return mask
    % bboxes = N x [x1 y1 width height]
    [foregroundMask, bboxes] = background.subtract(gray);
    cars = Car.empty;
    for k = 1 : length(bboxes)
        cars(k) = Car(bboxes(k,:), -1);
    end
    figure(2)
    imshow(foregroundMask);
    
    % filter all boxes that are not sparse
    SafeDistance = 3.0;
    isOk = ones(length(cars),1);
    for j = 1 : length(cars)
        center = cars(j).getCenter(); % [y x]
        expectedSize = roadCameraMap(center(1), center(2));
        for k = 1 : length(cars)
            if dist(center, cars(k).getCenter()') < expectedSize * SafeDistance
                isOk(j) = 0;
            end
        end
    end

    % filtering cars based on sizes
    SizeTolerance = 1.5;
    counter = 1;
    carsFilt = Car.empty;
    for k = 1 : length(cars)
        center = cars(k).getCenter(); % [y x]
        expectedSize = roadCameraMap(center(1), center(2));
        if expectedSize / SizeTolerance < cars(k).bbox(3) && ...
           expectedSize * SizeTolerance > cars(k).bbox(3)
            carsFilt(counter) = cars(k);
            counter = counter + 1;
        end
    end
    cars = carsFilt;
    
    
    % output
    frame_out = frame;
    for j = 1 : length(cars)
        tagColor = 'yellow';
        figure(1);
        frame_out = cars(j).drawCar(frame_out, tagColor);
    end
    imshow(frame_out);
    pause
    

end

clear frameWriter frameReader



