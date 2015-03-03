function laneEdges = computeHoughLanes(obj, frame)
    % Function to generate the lanes using hough transform
    % 
    % Usage:
    % GeometryObject.computeHoughLanes(frame);
    % Frame of the original image 
    % 
    % Might need optional arguments
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    warpedFrame = warpH(frame, obj.ipHomography, obj.warpSize);
    
    lines = findHoughLines(warpedFrame);    
    % Removing the lines if orientation is not vertical / nearly vertical
    for i = length(lines):-1:1
        if(abs(lines(i).theta - 0) > 5)
            lines(i) = [];
        end
    end
    
    % Debugging
    %debugImage = drawHoughLines(warpedFrame, lines);
    %figure(1); imshow(debugImage)
    
    % Getting the x co-ordinates of the line segments
    laneEdges = zeros(1, length(lines));
    for i = 1:length(lines)
        laneEdges(i) = mean(lines(i).point1(1), lines(i).point2(2));
    end
    
    % Debug image for visualization
    debug = false;
    if(debug)
        %debugImage = printDebugImage(frame, obj.road.vanishPt, imgPts);
        debugImage = drawHoughLines(frame, lines);
    end
end

% Drawing the lines detected by hough transform
function debugImage = drawHoughLines(frame, lines)
    % Debug image is the frame itself to begin with
    debugImage = frame;
    
    for i = 1 :length(lines)
        debugImage = drawLineSegment(debugImage, ...
                    lines(i).point1, lines(i).point2);
    end
end

% Find the hough lines (small wrapper)
function [houghLines, houghImage] = findHoughLines(image)
    
    % Getting the edge image and hough transformation
    edgeFrame = edge(rgb2gray(image), 'canny');
    [houghImage, theta, rho] = hough(edgeFrame);
    
    % Vertical lines are only to be considered
    % Detecting the lines
    peaks = houghpeaks(houghImage, 100, 'Threshold', 0.2*max(houghImage(:)));
    houghLines = houghlines(edgeFrame, theta, rho, peaks, 'FillGap', 10, 'MinLength', 5);
    
    % debugImage = drawHoughLines(image, houghLines);
    % figure(1); imshow(debugImage)
    % figure(2); imshow(edgeFrame)
end

% Generating the debug image i.e. Drawing the lane boundaries
function debugImage = printDebugImage(frame, vanishPoint, lanePoints)
    debugImage = frame;
    % Setting up the color and thickness
    laneThickness = 2;
    laneColor = uint8(reshape([255, 0, 0], [1 1 3]));
    
    blankImage= zeros(size(frame, 1), size(frame, 2));
    for i = 1:size(lanePoints, 2)
        blankImage = drawLineSegment(blankImage, vanishPoint, lanePoints(:, i));
    end
    blankImage = uint8(imdilate(blankImage > 0, ones(laneThickness)));
    
    debugImage = debugImage + ...
                    bsxfun(@times, blankImage, laneColor); 
end