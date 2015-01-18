function pretrainBackground (background, videoDir)
% train the background model from video
%   it is a workaround for the Matlab bug in saving / loading background
%   Hopefully, will find a solution to save the trained background

% validate inputs
parser = inputParser;
addRequired(parser, 'background', @(x) isa(x, 'BackgroundGMM'));
addRequired(parser, 'videoDir', @(x) exist(x, 'dir'));
parse (parser, background, videoDir);

videoPath = [videoDir '15-mins.avi'];
timesPath = [videoDir '15-mins.txt'];
frameReader = FrameReaderVideo (videoPath, timesPath); 
backimage = imread([videoDir 'models/backimage.png']);
for t = 1 : 100
    [img, ~] = frameReader.getNewFrame();
    img = uint8(int32(img) - int32(backimage) + 128);
    background.subtract(img, 'denoise', false);
end
clear frameReader
