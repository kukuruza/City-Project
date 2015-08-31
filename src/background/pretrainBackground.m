function pretrainBackground (background, videoPath, varargin)
% Train the background model using the first 100 frames of a video, 
%   so that the mask is ok right from the beginning of the main video
%
% input:
%   background - object of Background
%   videoPath

% validate inputs
parser = inputParser;
addRequired(parser, 'background', @(x) isa(x, 'Background'));
addRequired(parser, 'videoPath', @(x) exist(x, 'file'));
addParameter(parser, 'verbose', 0, @isscalar);
parse (parser, background, videoPath, varargin{:});
parsed = parser.Results;

inVideo  = vision.VideoFileReader(videoPath, 'VideoOutputDataType','uint8');
for t = 1 : 100
    [frame, eof] = step(inVideo);
    if eof, break; end
    result = background.step (frame);
    if parsed.verbose
        imshow([frame uint8(result(:,:,[1 1 1]))*255])
        waitforbuttonpress
    end
end
clear inVideo
