mask = imread('additionals/lanes578-closed.png');
load('additionals/578_tangent.mat');

%video = VideoWriter('roadSoupFilm.avi');
%video.FrameRate = 10;
%open(video);

yawMap = roadSoapFilm (tangent, 255 - mask, 'thresh', 0.001, 'verbose', 0);

%close(video)

imagesc(yawMap);
