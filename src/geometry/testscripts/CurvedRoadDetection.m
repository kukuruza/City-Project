% Script to detect and parameterize the curved road 
% 1. Split the image into portions, get hough lines (connected lines)
% 2. Estimate the vanishing point for each sub image
% 3. Fit a uniform B-spline through these points to get the road estimate
% 4. Also estimate the scale for the road to get adjacent lanes

% Setting up the paths from the environmental variables
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Reading the image, extracting images
image = imread('additionals/backimage-Mar15-10h.png');
% Get the edge map
edgeImg = edge(rgb2gray(image), 'canny');

% Split it into subsections
load('additionals/imageSections572.mat');
y = uint32([size(image, 1); y]);

% Get the hough lines in each section
debugImage = image;

segmentVP = [];
segmentBound = [];
segmentInliers = {};

for i = 1:length(y)-2
    endRow = y(i);
    startRow = y(i+1);
    
    % Finding the hough lines in the image section
    subImg = edgeImg(startRow:endRow, :);
    [houghImage, theta, rho] = hough(subImg);
    
    % Detecting the lines
    scaleLength = min(size(subImg));
    peaks = houghpeaks(houghImage, 100, 'Threshold', 0.1*max(houghImage(:)));
    houghLines = houghlines(subImg, theta, rho, peaks, 'FillGap', 10,...
                                        'MinLength', 0.1 * scaleLength);
    
    % Clean out unlikely candidates
    angleThreshold = 45;
    for j = length(houghLines):-1:1
        if(abs(houghLines(j).theta) > 45)
            houghLines(j) = [];
        end
    end
    
    %%%%%%%%%%%%%%%% Vote for vanishing lines in each section %%%%%%%%%%%%%
    % Finding the best set of inliers
    %bestInliers = ransacLineSegments(houghLines);
    %bestInliers = ones(length(houghLines), 1);
    
    %%%%%%%%%%%%%%% Find the mid-line approximation %%%%%%%%%%%%%%%%%%%%%
    subColorImg = image(startRow:endRow, :, :);
    lines = APPgetLargeConnectedEdges(...
                            rgb2gray(subColorImg), 10);
    
    % Aggregrating all the lines
    noHough = numel(houghLines);
    allLines = zeros(size(lines, 1) + noHough, 6);
    allLines(noHough+1:end, :) = lines;
    
    for j = 1:noHough
        allLines(j, [1 3 2 4 5 6]) = [houghLines(j).point1, houghLines(j).point2, ...
                            houghLines(j).theta, houghLines(j).rho];
    end
    
    if(0)
        % Plotting the lines in separate colors
        figure(2); hold off, imshow(subColorImg)
        figure(2); hold all, 
            plot(lines(1:noHough, [1 2])', lines(1:noHough, [3 4])', ...
                                                        'r', 'LineWidth', 2)
            plot(lines(noHough+1:end, [1 2])', lines(noHough+1:end, [3 4])', ...
                                                        'b', 'LineWidth', 2)
    end
    
    % Also giving the offset wrt y for the subimage
    [bestVP, inliers] = ransacVanishPoint(allLines, debugImage, double(startRow));
    
    % Storing the results across the sub frames
    segmentVP = [segmentVP; bestVP];
    boundary = [min([inliers(:, 1); inliers(:, 2)]), ...
                        max([inliers(:, 1); inliers(:, 2)])];
    segmentBound = [segmentBound; boundary];
    segmentInliers{i} = inliers;
    %pause()
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Find the B-spline for the midline using approximation
% Mean y co-ordinate is the horizon
horizon = mean(segmentVP(:, 2));

% Adjusted vanishing points (y co-ordinate is horizon)
adjVP = [segmentVP(:, 1), horizon * ones(size(segmentVP, 1), 1)];

scale = double(segmentBound(:, 2) - segmentBound(:, 1)) ./ ...
                            double((y(1:size(segmentBound, 1)) - horizon));
scale = scale / 2;
% meanScale = mean(scale)/2;

midPts = double([mean(segmentBound, 2), y(1:size(segmentBound, 1))]);
                        
% totalScale = [];
% for i = 1:numel(segmentInliers)
%     segScale = ([segmentInliers{i}(:, 1); segmentInliers{i}(:, 2)] - midPts(i, 1))./ ...
%                     ([segmentInliers{i}(:, 3); segmentInliers{i}(:, 4)] - horizon);
%     
%     totalScale = [totalScale; segScale];
% end                        

% First and last control points(three times each for ensuring they are on
% the B-spline
controlPts = zeros(7, 2);
startPt = adjVP(end, :);
endPt = double([mean(segmentBound(1, :)) y(1)]);

controlPts(1:3, :) = repmat(startPt, [3 1]);
controlPts(5:7, :) = repmat(endPt, [3 1]);
                    
% Vectors for the last three midpoints (normalized)
vecs = adjVP(end-3:end, :) - midPts(end-3:end, :);
vecs = bsxfun(@rdivide, vecs, hypot(vecs(:, 1), vecs(:, 2)));

beta1 = acosd(vecs(1, :) * vecs(2, :)');
beta2 = acosd(vecs(3, :) * vecs(2, :)');

angleThreshold = 10;

if beta2 < angleThreshold 
    % (beta1, beta2) = (*, 0)
    knotPt = midPts(end-3, :);
    
elseif beta1 < angleThreshold
    % (beta1, beta2) = (0, *)
    knotPt = midPts(end-2, :);
    
else
    % (beta1, beta2) = (0, 0)
    knotPt = mean(midPts(end-2, :), midPts(end-3, :));
end

% Middle control Pt
controlPts(4, :) = 1.5 * knotPt - 0.25 * (startPt + endPt);

% Getting the points for interpolation
points = drawUniformSpline(controlPts, 0.001);

% Drawing the other edges
outerPoints = {};
innerPoints = {};

for i = 1:length(scale)
    outerCPts = controlPts;
    outerCPts(4:7, :) = outerCPts(4:7, :) + ...
                    [scale(i) * (outerCPts(4:7, 2) - horizon), zeros(4, 1)];
    outerPoints{i} = drawUniformSpline(outerCPts, 0.001);

    innerCPts = controlPts;
    innerCPts(4:7, :) = innerCPts(4:7, :) - ...
                    [scale(i) * (innerCPts(4:7, 2) - horizon), zeros(4, 1)];
    innerPoints{i} = drawUniformSpline(innerCPts, 0.001);
end
% Debugging
if(1)
    figure(1); hold off
        imshow(image)
    figure(1); hold on 
        %plot(midPts(:, 1), midPts(:, 2), 's', 'LineWidth', 3)
        %plot(controlPts(:, 1), controlPts(:, 2), 's', 'LineWidth', 10)
        %plot(segmentBound(:, 1), y(1:end-1), 'x', 'LineWidth', 3)
        %plot(segmentBound(:, 2), y(1:end-1), 'x', 'LineWidth', 3)
        %plot(adjVP(:, 1), adjVP(:, 2), '*', 'LineWidth', 3)
        plot(points(:, 1), points(:, 2), '.', 'LineWidth', 1)
        for i = 1:length(scale)
            plot(outerPoints{i}(:, 1), outerPoints{i}(:, 2), '.', 'LineWidth', 1)
            plot(innerPoints{i}(:, 1), innerPoints{i}(:, 2), '.', 'LineWidth', 1)
        end
    hold off 
end
