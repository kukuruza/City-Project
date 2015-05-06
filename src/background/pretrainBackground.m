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
addParameter(parser, 'verbose', 0, @isscalar);
parse (parser, background, videoPath, varargin{:});
parsed = parser.Results;

frameReader = FrameReaderVideo (videoPath); 
for t = 1 : 100
    [img, ~] = frameReader.getNewFrame();
    if ~isempty(parsed.backimage)
        img = image2ghost(img, parsed.backimage);
    end
    result = background.subtract(img, 'denoise', false);
    if parsed.verbose
        imshow([img uint8(result(:,:,[1 1 1]))*255])
        waitforbuttonpress
    end
end
clear frameReader
