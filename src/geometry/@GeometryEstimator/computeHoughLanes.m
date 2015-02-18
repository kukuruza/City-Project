function [ lanes ] = computeHoughLanes(obj, frame)
    % Function to generate the lanes using hough transform
    % 
    % Usage:
    % GeometryObject.computeHoughLanes(frame);
    % Frame of the original image 
    % 
    % Might need optional arguments
    
    % Assinging the outputs to avoid function errors
    lanes = [];
    
    %lines = findHoughLines(frame);    
    %debugImage = drawHoughLines(frame, lines);
    %figure(1); imshow(debugImage)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    warpedFrame = warpH(frame, obj.ipHomography, obj.warpSize);
    
    lines = findHoughLines(warpedFrame);    
    % Removing the lines if orientation is not vertical / nearly vertical
    for i = length(lines):-1:1
        if(abs(lines(i).theta - 0) > 5)
            lines(i) = [];
        end
    end
    debugImage = drawHoughLines(warpedFrame, lines);
    figure(1); imshow(debugImage)
    % Comparing warped edges and edges of warped frame
    %warpedEdges = warpH(edgeFrame, obj.ipHomography, obj.warpSize);
    %edgeWarp = edge(rgb2gray(warpedFrame), 'canny');
    
    %figure(1); imagesc(warpedEdges)
    %figure(2); imagesc(edgeWarp)
    
    %figure(2); imagesc(edgeFrame)
    %figure(3); imshow(warpedFrame)
    
    % Debug image for visualization
    debug = false;
    if(debug)
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
    
    %debugImage = drawHoughLines(image, houghLines);
    %figure(1); imshow(debugImage)
    figure(2); imshow(edgeFrame)
end