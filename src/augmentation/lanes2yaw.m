% angles: counter-clockwise, zero angle is oriented along X 

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


% TODO: do this for each connected conponent separately

lanes_template = 'models/cam717/google1/lane*.png';

im = imread([CITY_DATA_PATH 'models/cam717/google1/lane*.png']);
im = rgb2gray(im);
im = double(im);

rad = 20;
MinPoints4Fitting = rad;
verbose = 0;

% prepare filters for figuring out direction. 
%   could make a filter for each pixel with exact direction, but it's slow
% filter 'up to down' looks like this:
%   0 0
%   1 1
filter = zeros(rad*4+1, rad*4+1);
filter (rad*2+1 : end, :) = 1;
filters = zeros (rad*2+1, rad*2+1, 5);
for i = 1 : 5
    filters(:,:,i) = filter(rad+1 : end-rad, rad+1 : end-rad);
    filter = imrotate (filter, 45, 'nearest', 'crop');
    if verbose, subplot(1,5,i); imshow(filters(:,:,i)*255); end
end

% manage borders by adding transparent pixels
im = padarray (im, [rad, rad], 0);

% array of angles
angles = zeros(size(im));
responses = zeros(size(im));

counter = 1;
for y = rad+1 : size(im,1)-rad
    for x = rad+1 : size(im,2)-rad
        
        % skip all black pixels
        if im(y,x) == 0, continue; end
        
        neighborhood = im(y-rad : y+rad, x-rad : x+rad);
        [ys, xs] = find (neighborhood > 0);
        if length(xs) < MinPoints4Fitting, continue; end

        % Fitting a curve
        % Curve of degree two
        %curve = polyfit(x, y, 2);
        % Curve of degree one
        curve = polyfit(xs, ys, 1);

        % Finding the tangent at that point
        %tangent = 2 * xPts(i) * curve(1) + curve(2);
        tangent = curve(1);
        angle = -atand(tangent);
        
        % pick the filter with the closest angle from the list
        [~, ind] = min(abs(angle - [-90, -45, 0, 45, 90]));
        filter = filters(:,:,ind);
        % first half of the filter is all ones, the second half is zeros
        response1 = conv2 (neighborhood, filter, 'valid');
        norm1     = conv2 (double(neighborhood > 0), filter, 'valid');
        % second half of the filter is all minus ones, the first -- zeros
        filter = filter - 1;
        response2 = conv2 (neighborhood, filter, 'valid');
        norm2     = conv2 (double(neighborhood > 0), filter, 'valid');
        % difference between normalized outputs from two halves
        response = response2 / norm2 - response1 / norm1;
        if response < 0, angle = angle + 180; end
        responses(y,x) = response;
        
        % we want the range [0, 360)
        angles(y, x) = mod(angle, 360);
        counter = counter + 1;
        
    end
end

% crop to original size
angles = angles(rad+1 : end-rad, rad+1 : end-rad);

% we'll write half precision to fit into uint8 [0, 255]
angles = angles / 2;
assert (all(all(angles >= 0 & angles <= 255)));
% write in color
%angles = cat(3, angles, zeros(size(angles)), zeros(size(angles)));
imwrite (uint8(angles), '/Users/evg/Desktop/3Dmodel/572-ground-angles2.png');
