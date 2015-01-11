close all; clear all;

frame = imread('../cam572.png');
mask = imread('../curvedroadmap.jpg');

mask = uint8(mask ~= 0);
mask = 255 * mask(:, :, [ 1 1 1]); 

paintedFrame = frame * 0.7 + 0.3 * mask;
imshow(paintedFrame)