function pretrainBackground (background, videoDir, varargin)
% train the background model from video using GHOST frames.
%   it is a workaround for the Matlab bug in saving / loading background
%   Hopefully, will find a solution to save the trained background
%
% input:
%   background - object of BackgroundGMM
%   videoDir
%   'ghost', true/false. If true (default) will use ghost image to train

% validate inputs
parser = inputParser;
addRequired(parser, 'background', @(x) isa(x, 'BackgroundGMM'));
addRequired(parser, 'videoDir', @(x) exist(x, 'dir'));
addParameter(parser, 'ghost', true, @(x) isscalar(x) && islogical(x));
parse (parser, background, videoDir, varargin{:});
parsed = parser.Results;

videoPath = [videoDir '15-mins.avi'];
timesPath = [videoDir '15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 
backimage = imread([videoDir 'models/backimage.png']);
for t = 1 : 100
    [img, ~] = frameReader.getNewFrame();
    if parsed.ghost
        img = uint8(int32(img) - int32(backimage) + 128);
    end
    background.subtract(img, 'denoise', false);
end
clear frameReader
