% Use GMM model to extract foreground masks from 'in_image_videopath'
%   The mask video is written to 'out_mask_videopath'

clear all

% set path
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

% input
in_image_video = 'camdata/cam572/Oct28-10h';
in_image_videopath = [CITY_DATA_PATH in_image_video '.avi'];

% output
out_mask_videopath = [CITY_DATA_PATH in_image_video '-mask.avi'];

% what to do
write = true;
show = false;



%% work

% init backgroudn model
background = Background();
pretrainBackground (background, in_image_videopath);

% init video
frameReader = vision.VideoFileReader(in_image_videopath, 'VideoOutputDataType','uint8');
maskWriter = FrameWriterVideo (out_mask_videopath, 2);

for t = 0 : 10000000
    if mod(t, 100) == 0, fprintf ('frame: %d\n', t); end

    [frame, eof] = step(frameReader);
    mask = background.step(frame);
    if show
        subplot(1,2,1), imshow(frame);
        subplot(1,2,2), imshow(mask);
        pause(0.5);
    end
    if write
        maskWriter.step(uint8(mask)*255);
    end
    
    if eof, break; end
end

clear frameReader maskWriter background

