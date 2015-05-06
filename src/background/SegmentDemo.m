% test that the background subtraction class works the same way
%   as the original Lynna's code
%
% Ctrl+C to interrupt unfortunately


clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input and ground truth
imagesDir = [CITY_DATA_PATH 'camdata/cam572/2-hours/'];
outImagePath = [CITY_DATA_PATH 'testdata/background/result/'];


%% test

frameReader = FrameReaderImages (imagesDir);
background = Background();


% background subtraction
background.num_training_frames = 5;
background.initial_variance = 30;

% mask refinement
background.fn_level = 15;
background.fp_level = 1;

% extracting bounding boxes
background.minimum_blob_area = 50;
         
N=0;
while true
    frame = frameReader.getNewFrame();
    %[mask, bboxes] = subtractor.subtract(frame);
    [mask, bboxes] = background.subtract (frame);
    %bboxes
    frame_out = background.drawboxes(frame, bboxes);
    subplot(1,2,1),imshow(frame_out);
    subplot(1,2,2),imshow(mask);
    imname = sprintf('result%d.png',N);
    %imwrite(mask,fullfile(outImagePath,imname));
    pause(0.5);
    N=N+1;
end
