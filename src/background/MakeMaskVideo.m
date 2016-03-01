function MakeMaskVideo (in_video_dir, varargin)
% Use GMM model to extract foreground masks from 'in_image_videofile'
%   The mask video is written to 'out_mask_videopath'
%
% Args:
%  in_image_videofile - is relative to CITY_DATA_PATH, e.g. 'camdata/cam125/Feb07-08h'
%  LearningRate       - for GMM background


% set path
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% parsing input
parser = inputParser;
addRequired(parser,  'in_image_videofile',  @ischar);
addParameter(parser, 'LearningRate',        0.005, @isscalar);
addParameter(parser, 'verbose',             0, @isscalar);
parse (parser, in_video_dir, varargin{:});
parsed = parser.Results;



%% input

% input
in_image_videopath = fullfile(CITY_DATA_PATH, in_video_dir, 'src.avi');

% output
out_mask_videofile = fullfile(in_video_dir, 'mask.avi');

% what to do
write = true;
show = false;



%% work

% init backgroudn model
background = Background('LearningRate', parsed.LearningRate);
pretrainBackground (background, in_image_videopath);

% init video
frameReader = vision.VideoFileReader(in_image_videopath, 'VideoOutputDataType','uint8');
maskWriter = FrameWriterVideo (out_mask_videofile, 2);

for t = 0 : 10000000
    if mod(t, 500) == 0, fprintf ('frame: %d\n', t); end

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

