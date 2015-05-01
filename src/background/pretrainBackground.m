function pretrainBackground (background, videoPath, varargin)
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
addRequired(parser, 'videoPath', @(x) exist(x, 'file'));
addParameter(parser, 'backimage', []);
parse (parser, background, videoPath, varargin{:});
parsed = parser.Results;

frameReader = FrameReaderVideo (videoPath); 
for t = 1 : 100
    [img, ~] = frameReader.getNewFrame();
    if parsed.backimage
        img = uint8(int32(img) - int32(backimage) + 128);
    end
    background.subtract(img, 'denoise', false);
end
clear frameReader
