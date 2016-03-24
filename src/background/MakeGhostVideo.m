function MakeGhostVideo (in_video_dir, varargin)
% Args:
%  in_video_dir       - relative to CITY_DATA_PATH, e.g. 'camdata/cam125/Feb07-08h'
%  in_src_name        - defaults to 'src.avi', name of the original video
%  in_back_name       - defaults to 'back.avi', name of the background video

% parsing input
parser = inputParser;
addRequired(parser,  'in_video_dir',        @ischar);
addParameter(parser, 'in_src_name',         'src.avi', @ischar);
addParameter(parser, 'in_back_name',        'back.avi', @ischar);
addParameter(parser, 'verbose',             0, @isscalar);
parse (parser, in_video_dir, varargin{:});
parsed = parser.Results;

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input

% input
in_image_videopath = fullfile(CITY_DATA_PATH, in_video_dir, parsed.in_src_name);
in_back_videopath  = fullfile(CITY_DATA_PATH, in_video_dir, parsed.in_back_name);

% output
out_ghost_file      = fullfile(in_video_dir, 'ghost.avi');

% what to do
write = true;
show = false;

verbose = parsed.verbose;



%% work

% objects to detect background, to read video, and to write results video
frameReader  = vision.VideoFileReader(in_image_videopath, 'VideoOutputDataType','uint8');
backReader   = vision.VideoFileReader(in_back_videopath, 'VideoOutputDataType','uint8');
if write
    ghostWriter = FrameWriterVideo (out_ghost_file, 2);
end

for t = 1 : 1000000
    if mod(t, 500) == 0, fprintf ('frame: %d\n', t); end
    
    % read image and mask
    [frame, eof1] = frameReader.step();
    [back,  eof2] = backReader.step();
    assert (all(size(frame) == size(back)));

    ghost = patch2ghost(frame, back);

    if write
        ghostWriter.step (ghost);
    end

    if show
        imshow([frame, back, ghost]);
        pause (0.5);
    end
    
    assert (eof1 && eof2 || ~eof1 && ~eof2)
    if eof1, break, end
end

% clearing will save videos to disk
clear frameReader backReader ghostWriter
