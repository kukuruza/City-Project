% GenerateBackimage -- makes it up for a missing function in Background
%   It generates a ghost and background videos from image video,
%   for every pixel the most recent frame that contained background is picked

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input

% input
in_image_video = 'camdata/cam572/Nov28-10h';
in_image_videopath  = [CITY_DATA_PATH in_image_video '.avi'];
in_mask_videopath   = [CITY_DATA_PATH in_image_video '-mask.avi'];
%in_ref_backpath     = [CITY_DATA_PATH 'models/backimage.png'];

BackLearnR = 0.2;

% output
out_background_path = [in_image_video '-back.avi'];
out_ghost_path      = [in_image_video '-ghost.avi'];

% what to do
write = true;
show = false;



%% work

% objects to detect background, to read video, and to write results video
frameReader  = vision.VideoFileReader(in_image_videopath, 'VideoOutputDataType','uint8');
maskReader   = vision.VideoFileReader(in_mask_videopath, 'VideoOutputDataType','uint8');
if write
    backWriter  = FrameWriterVideo (out_background_path, 2);
    ghostWriter = FrameWriterVideo (out_ghost_path, 2);
end

% load reference clean background if exists
if exist('in_ref_backpath', 'var')
    refBackImage = imread(in_ref_backpath);
end

for t = 1 : 1000000
    if mod(t, 100) == 0, fprintf ('frame: %d\n', t); end
    
    % read image and mask
    [frame, eof1] = frameReader.step();
    [mask,  eof2] = maskReader.step();
    assert (all(size(frame) == size(mask)));
    mask = mask > 128; % deal with jpg compression artifacts

    % increase the mask size
    DilateRadius = 1;
    seDilate = strel('disk', DilateRadius);
    mask = imdilate(mask, seDilate);
    
    % at the 1st frame
    if ~exist('backImage', 'var')
        backImage = frame;
    end
    
    % paint the unmasked part of the image
    backImage(~mask) = frame(~mask) * BackLearnR + backImage(~mask) * (1 - BackLearnR);
    
    % use generateCleanBackground algorithm, if enabled
    if exist('refBackImage', 'var')
        backImage = generateCleanBackground (refBackImage, backImage, 'verbose', 0);
    end

    ghost = patch2ghost(frame, backImage);

    if write
        backWriter.step (backImage); 
        ghostWriter.step (ghost);
    end

    if show
        imshow([frame, backImage ghost]);
        pause (0.5);
    end
    
    assert (eof1 && eof2 || ~eof1 && ~eof2)
    if eof1, break, end
end

clear frameReader maskReader backWriter ghostWriter
