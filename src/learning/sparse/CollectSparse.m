% Collect good frames and bboxes
% Can work with any implementation of io.FrameReaderInterface,
%   but designed to be used to read stuff from internet.
%
% Reads a frame and detects bboxes using some detectors.
%   If satisfied, saves the frame and bboxes to videos and to database
%
% 'Strategy' input


clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

% input
camera = 572;
num_pretrain = 20;
num_images = 18;

% strategy
%Strategy = 'AllCarsDetectedByBothDetectors';
Strategy = 'DetectionByOneDetectorIsEnough';

% parameters
BackLearnR = 0.2;
ThresholdScore = 0.98;  % required confindence for background detector
ThresholdMatch = 0.5;   % required IoU for matching
ThresholdWidth = 20;    % required to consider a car


% output
image_video_path = 'camdata/cam572/test.avi';
ghost_video_path = 'camdata/cam572/test-ghost.avi';
back_video_path  = 'camdata/cam572/test-back.avi';
mask_video_path  = 'camdata/cam572/test-mask.avi';
db_path = 'databases/sparse/572-test/src.db';

% what to do
write = true;
show = true;

verbose = 1;



%% init

% background
background = Background();

% detectors
detector1 = FrombackDetector();
model_dir = fullfile(getenv('FASTERRCNN_ROOT'), 'output/faster_rcnn_final/faster_rcnn_VOC0712_vgg_16layers');
detector2 = FasterRcnnDetector(model_dir, 'use_gpu', true);
%detector2 = CascadeCarDetector('learning/violajones/models/May17-high-yaw/ex0.1-noise1.5-pxl5/cascade.xml');

% backend to read frame from internet
%imgReader = FrameReaderInternet (camera);
imgReader = FrameReaderVideo ('camdata/cam572/Oct30-17h.avi', []);
imgReader.verbose = verbose;

% backend to write frames to video
imgWriter = ImgDbWriterVideo();

% open database
if write
    c = dbCreate (fullfile(CITY_DATA_PATH, db_path));
end

% pretrain background
fprintf ('pre-training background started...\n');
for t = 1 : num_pretrain
    frame = imgReader.getNewFrame();
    background.step (frame);
end
fprintf ('pre-training background done.\n');



%% work

counter = 0;
for t = 0 : num_images-1
    fprintf ('frame %d:\n', t);

    % get frame and mask
    [frame, timestamp] = imgReader.getNewFrame();
    mask = background.step (frame);

    % at the 1st frame
    if ~exist('backImage', 'var')
        backImage = frame;
    end
    
    % mask for backimage
    DilateRadius = 1;
    seDilate = strel('disk', DilateRadius);
    maskBack = imdilate(mask, seDilate);
    maskBack = maskBack(:,:,[1,1,1]);
    
    % get backimage and ghost
    backImage(~maskBack) = frame(~maskBack) * BackLearnR + backImage(~maskBack) * (1 - BackLearnR);
    ghost = patch2ghost(frame, backImage);
    

    % detect cars
    tic
    cars1 = detector1.detect(mask);
    cars2 = detector2.detect(ghost);
    toc

    % put scores into a separate array
    scores1 = ones(length(cars1), 1);
    for j = 1 : length(cars1)
        scores1(j) = cars1(j).score;
        if verbose > 1, fprintf('  background detector score: %f\n', cars1(j).score); end
    end
    scores2 = ones(length(cars2), 1);
    for j = 1 : length(cars2)
        scores2(2) = cars2(2).score;
        if verbose > 1, fprintf('  violajones detector score: %f\n', cars2(j).score); end
    end
    
    
    % filter by score
    cars1(scores1 < ThresholdScore) = [];
    cars2(scores2 < ThresholdScore) = [];

    if verbose
        fprintf ('detected cars from detector1: %d\n', length(cars1));
        fprintf ('detected cars from detector2: %d\n', length(cars2));
    end

    % find well-intersecting detections
    matches = matchCarSets (cars1, cars2, ThresholdMatch);
    cars = Car.empty();
    for j = 1 : size(matches,1)
        cars = [cars; cars1(matches(j,1)); cars2(matches(j,2))];
    end
    if verbose, fprintf('found %d cars found by both detectors.\n', length(cars)/2); end
    
    if isempty(cars)
        fprintf ('ignore frame -- no cars found by both detectors.\n');
        continue;
    end
    
    if strcmp(Strategy, 'AllCarsDetectedByBothDetectors')
        % if there are unmatched cars, ignore this frame
        num_unmatched = 0;
        for j = 1 : length(cars1)
            if isempty(find(matches(:,1) == j, 1)) && cars1(j).bbox(3) > ThresholdWidth
                num_unmatched = num_unmatched + 1;
            end
        end
        for j = 1 : length(cars2)
            if isempty(find(matches(:,2) == j, 1)) && cars2(j).bbox(3) > ThresholdWidth
                num_unmatched = num_unmatched + 1;
            end
        end
        if num_unmatched > 0
            fprintf ('ignore frame -- %d unmatched cars.\n', num_unmatched);
            continue;
        end
        
    elseif strcmp(Strategy, 'DetectionByOneDetectorIsEnough')
        % there is high probability of some cars left undetected
        ; % do nothing
    
    fprintf ('approved this frame.\n');
    counter = counter + 1;
    
    % write
    if write
        imgWriter.imwrite(frame, image_video_path);
        imgWriter.maskwrite(mask, mask_video_path);
        imgWriter.imwrite(backImage, back_video_path); 
        imgWriter.imwrite(ghost, ghost_video_path);
        
        imagefile = fullfile(image_video_path(1:end-4), sprintf('%010d', t));
        maskfile  = fullfile(mask_video_path (1:end-4), sprintf('%010d', t));
        query = 'INSERT INTO images(imagefile,maskfile,width,height,src,time) VALUES (?,?,?,?,?,?)';
        sqlite3.execute(c, query, imagefile, maskfile, size(frame,2), size(frame,1), sprintf('%d',camera), timestamp);

        for j = 1 : length(cars)
            car = cars(j);
            bbox = car.bbox;
            query = 'INSERT INTO cars(imagefile,name,x1,y1,width,height,score) VALUES (?,?,?,?,?,?,?)';
            sqlite3.execute(c, query, imagefile, 'vehicle', bbox(1), bbox(2), bbox(3), bbox(4), car.score);
        end
    end
    
    % show
    if show
        mask  = uint8(mask(:,:,[1,1,1])) * 255;
        mask = drawCars(mask, cars1, 'color', 'red');
        mask = drawCars(mask, cars2, 'color', 'blue');
        mask = drawCars(mask, cars);
        subplot(2,1,1), imshow(mask);
        subplot(2,1,2), imshow(frame);
        pause()
    end
end

if write
    sqlite3.close(c);
    imgWriter.close();
end

fprintf ('statistics: wrote %d frames out of %d.\n', counter, t+1);

