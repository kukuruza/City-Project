function MakeBackVideo (in_video_dir, varargin)
% MakeBackVideo -- makes it up for a missing function in Background
%   It generates a ghost and background videos from image video,
%   for every pixel the most recent frame that contained background is picked
%
% Args:
%  in_image_videofile - relative to CITY_DATA_PATH, e.g. 'camdata/cam125/Feb07-08h'
%  in_ref_backfile    - relative to CITY_DATA_PATH, e.g. 'camdata/cam125/Feb07-08h-back.png'
%                       if provided, background will be cleaned w.r.t. it
%  DilateRadius       - mask is dilated on this ammount
%  BackLearnRate      - learning rate: how fast background is updated
%  FilterSigmaCoef    - used by generateCleanBackground when in_ref_backfile provided

% parsing input
parser = inputParser;
addRequired(parser,  'in_image_videofile',  @ischar);
addParameter(parser, 'DilateRadius',        1, @isscalar);
addParameter(parser, 'BackLearnRate',       0.2, @isscalar);
addParameter(parser, 'FilterSigmaCoef',     0.05, @isscalar);
addParameter(parser, 'in_ref_backfile',     '', @ischar);
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
in_image_videopath  = fullfile(CITY_DATA_PATH, in_video_dir, 'src.avi');
in_mask_videopath   = fullfile(CITY_DATA_PATH, in_video_dir, 'mask.avi');
in_ref_backfile     = parsed.in_ref_backfile;

% parameters
DilateRadius = parsed.DilateRadius;
BackLearnRate = parsed.BackLearnRate;
FilterSigmaCoef = parsed.FilterSigmaCoef;

% output
out_background_file = fullfile(in_video_dir, 'back.avi');
out_ghost_file      = fullfile(in_video_dir, 'ghost.avi');

% what to do
write = true;
show = false;

verbose = parsed.verbose;



%% work

% objects to detect background, to read video, and to write results video
frameReader  = vision.VideoFileReader(in_image_videopath, 'VideoOutputDataType','uint8');
maskReader   = vision.VideoFileReader(in_mask_videopath, 'VideoOutputDataType','uint8');
if write
    backWriter  = FrameWriterVideo (out_background_file, 2);
    ghostWriter = FrameWriterVideo (out_ghost_file, 2);
end

% load reference clean background if exists
if ~isempty(in_ref_backfile)
    refBackImage = imread([CITY_DATA_PATH in_ref_backfile]);
end

for t = 1 : 1000000
    if mod(t, 500) == 0, fprintf ('frame: %d\n', t); end
    
    % read image and mask
    [frame, eof1] = frameReader.step();
    [mask,  eof2] = maskReader.step();
    assert (all(size(frame) == size(mask)));
    mask = mask > 128; % deal with jpg compression artifacts

    % increase the mask size
    seDilate = strel('disk', DilateRadius);
    mask = imdilate(mask, seDilate);
    
    % at the 1st frame
    if ~exist('backImage', 'var')
        backImage = frame;
    end
    
    % paint the unmasked part of the image
    backImage(~mask) = frame(~mask) * BackLearnRate + backImage(~mask) * (1 - BackLearnRate);
    
    % use generateCleanBackground algorithm, if enabled
    if ~isempty(in_ref_backfile)
        backImage = generateCleanBackground (refBackImage, backImage, ...
                                             'FilterSigmaCoef', FilterSigmaCoef, ...
                                             'verbose', verbose);
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

% clearing will save videos to disk
clear frameReader maskReader backWriter ghostWriter
