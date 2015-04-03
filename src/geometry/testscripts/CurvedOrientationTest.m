close all; clear all;
addpath('../')
addpath('additionals/')

run ../../rootPathsSetup.m
run ../../subdirPathsSetup.m

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%warpedImg = imread('additionals/warped578.png');
laneImg = imread('additionals/lanes578.jpg');
laneImg = laneImg(:, :, 1);
% Adjusting the size to the original image size
laneImg = [repmat(laneImg(:, 1), [1 5]), laneImg]; 
%lanes = uint8([lanes(:, 1:5, :), lanes] > 1);

lanes = (laneImg > 250);
%lanes = uint8([lanes(:, 1:5, :), lanes] > 1);

% For every pixel on the lanes, take a neighborhood, approximate it by a
% second degree polynomial and find the slope at that point
[yPts, xPts] = find(lanes == 0);

% Check if the indices have same size
assert(length(xPts) == length(yPts))

tangent = zeros(size(lanes, 1), size(lanes, 2));
for i = 1:length(xPts)
    % Take the neighborhood
    %fprintf('%f %f \n', xPts(i), yPts(i));
    hNbrSize = 3;
    
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
    
    if(length(x) > 2)
        % Fitting a curve
        % Curve of degree two
        %curve = polyfit(x, y, 2);
        % Curve of degree one
        curve = polyfit(x, y, 1);
            
        % Finding the tangent at that point
        %tangent(yPts(i), xPts(i)) = atand(2 * xPts(i) * curve(1) + curve(2));
        tangent(yPts(i), xPts(i)) = atand(curve(1));
    end
end

%figure(1); imagesc(tangent)

% Adhoc way to deal with top part and lower part
Gdir = tangent;
Gind = lanes == 0;
I = tangent;

for i = 140:size(Gdir, 1)
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

for i = 80:140
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
        laneMarks = [laneMarks(1), laneMarks(end)];
        
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

% Reading the road mask file and assigning the directions
dir578 = {'out', 'out', 'out', 'none', 'in', 'in', 'in'};
roadMask = imread('additionals/roadMask578.tiff');

lanes = unique(roadMask);
for i = 1:numel(dir578)
    mask = roadMask == i;
    if(strcmp(dir578{i}, 'in'))
        I(mask) = I(mask) - 180;
    elseif(strcmp(dir578{i}, 'none'))
        I(mask) = 0;
    end
end

figure; imagesc(I)

