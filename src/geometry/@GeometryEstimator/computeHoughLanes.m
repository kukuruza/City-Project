function [ verticalLines ] = computeHoughLanes(obj, frame)
    % Function to generate the lanes using hough transform
    % 
    % Usage:
    % GeometryObject.computeHoughLanes(frame);
    % Frame of the original image 
    % 
    % Might need optional arguments
    
    % Assinging the outputs to avoid function errors
    verticalLines = [];
    
    % Getting the edge image and hough transformation
    edgeFrame = edge(rgb2gray(frame), 'canny');
    [houghFrame, theta, rho] = hough(edgeFrame);
    
    % Vertical lines are only to be considered
    % Detecting the lines
    peaks = houghpeaks(houghFrame, 100);
    lines = houghlines(edgeFrame, theta, rho, peaks, 'FillGap', 10, 'MinLength', 10);
    
    debugImage = drawHoughLines(frame, lines);
    %figure(1); imshow(debugImage)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    warpedFrame = warpH(frame, obj.ipHomography, obj.warpSize);
    
    edgeFrame = edge(rgb2gray(warpedFrame), 'canny');
    [houghFrame, theta, rho] = hough(edgeFrame);
    % Vertical lines are only to be considered
    % Detecting the lines
    peaks = houghpeaks(houghFrame, 100);
    lines = houghlines(edgeFrame, theta, rho, peaks, 'FillGap', 10, 'MinLength', 5);
    
    length(lines)
    % Removing the lines if orientation is not vertical / nearly vertical
    for i = length(lines):-1:1
        if(abs(lines(i).theta - 0) > 5)
            lines(i) = [];
        end
    end
    length(lines)
    
    debugImage = drawHoughLines(warpedFrame, lines);
    %figure(2); imshow(debugImage)
    % Comparing warped edges and edges of warped frame
    %warpedEdges = warpH(edgeFrame, obj.ipHomography, obj.warpSize);
    %edgeWarp = edge(rgb2gray(warpedFrame), 'canny');
    
    %figure(1); imagesc(warpedEdges)
    %figure(2); imagesc(edgeWarp)
    
    %figure(2); imagesc(edgeFrame)
    %figure(3); imshow(warpedFrame)
    
    %if(false)
    %vertlines = [];
    %for i = numel(lines):-1:1        
    %    if(abs(lines(i).theta - 0) < 5)
    %        vertlines = [vertlines, lines(i)];
    %    end
    %end
    
    %verticalLines = vertlines;
    
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
