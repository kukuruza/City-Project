close all; clear all;
addpath('../')
addpath('additionals/')
run ../../rootPathsSetup.m
run ../../subdirPathsSetup.m

cameraId = 578;
%image = imread(fullfile('~/Google Drive/City-Project/data/camdata', ...
%               sprintf('cam%d', cameraId), 'frames-4pm', 'image0001.png'));
image = imread('test.png');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%warpedImg = imread('additionals/warped578.png');
laneImg = imread('~/Desktop/shortlanes.jpg');
%lanes = uint8([lanes(:, 1:5, :), lanes] > 1);
lanes = (laneImg > 250);

% For every pixel on the lanes, take a neighborhood, approximate it by a
% second degree polynomial and find the slope at that point
[yPts, xPts] = find(lanes == 0);

% Check if the indices have same size
assert(length(xPts) == length(yPts))

tangent = zeros(size(lanes, 1), size(lanes, 2));
for i = 1:length(xPts)
    % Take the neighborhood
    %fprintf('%f %f \n', xPts(i), yPts(i));
    hNbrSize = 5;
    
    leftExt = max(1, xPts(i)-hNbrSize);
    rightExt = min(size(lanes, 2), xPts(i) + hNbrSize);
    
    topExt = max(1, yPts(i) - hNbrSize);
    bottomExt = min(size(lanes, 1), yPts(i) + hNbrSize);
    
    % Checking out of bounds error
%     fprintf('%d\n%d\n%d\n%d\n', leftExt, ...
%                                 rightExt, ...
%                                 bottomExt, ...
%                                 topExt);
  
    nbrPts = lanes(topExt:bottomExt, leftExt:rightExt);
    [x, y] = find(nbrPts == 0);
    
    if(length(x) > 4)
        % Fitting a curve
        %fprintf('%d\n', length(x));
        curve = polyfit(x, y, 2);
    
        % Finding the tangent at that point
        tangent(yPts(i), xPts(i)) = atand(2 * xPts(i) * curve(1) + curve(2));
    end
    
    %figure(1); imagesc(nbrPts)
    %fprintf('%d %d %d\n', size(nbrPts), length(x));
    
    % Finding the 
end
figure(1); imagesc(tangent)
return
marked = image .* lanes(:, :, [1 1 1]);
[~, Gdir] = imgradient(lanes(:, :, 1));
[gx, gy] = derivative5(lanes(:, :, 1), 'x', 'y');
angle = atan2d(gx, gy);

figure(1); imagesc(angle)
figure(2); imagesc(Gdir)
break
% Consider only negative directions of the gradient
Gind = Gdir < 0;
%Gdir = Gdir(Gind);
%figure(1); imshow(Gind)
%figure(2); imshow(Gdir)
%return

% Now go through each row and get the start of the lanes
I = Gdir;
laneSize = zeros(1, size(Gdir, 1));
figure(1); imagesc(Gdir)
return

for i = 80:size(Gdir, 1)
    % Checking for non-zero entries, if number is greater than 
    nonZero = [];
    nonZero = find(Gind(i, :) > 0);
    
    if(length(nonZero) > 4)
        laneMarks = [];
        % Find those points which are not close
        for j = 1:length(nonZero)-1
            if(nonZero(j) < nonZero(j+1) - 5)
                laneMarks = [laneMarks, nonZero(j)];
            end
        end
        laneMarks = [laneMarks, nonZero(end)];
        
        % Interpolating between the points linearly
        for j = 1:length(laneMarks)-1
            ratio = linspace(0, 1, laneMarks(j+1)-laneMarks(j)+1);
            %fprintf('Interpolating: (%f %f)\n', ...
            %                        I(i, laneMarks(j)), I(i, laneMarks(j+1)));
            
            I(i, laneMarks(j):laneMarks(j+1)) = ratio * I(i, laneMarks(j+1)) + ...
                                        (1-ratio) * I(i, laneMarks(j));
        end
    end
end

figure(1); imagesc(I)

% Perform linear interpolation to get the intermediate values
%[rowId, colId, vals] = find(Gdir < 0);
%interpolated = interp2(colId, rowId, vals, 1:size(Gdir, 2), 1:size(Gdir, 1));
