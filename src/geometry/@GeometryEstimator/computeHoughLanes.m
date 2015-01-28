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
    grayFrame = rgb2gray(frame);
    edgeFrame = edge(grayFrame, 'canny');
    [houghFrame, theta, rho] = hough(edgeFrame);
    
    % Vertical lines are only to be considered
    % Detecting the lines
    peaks = houghpeaks(houghFrame, 20);
    lines = houghlines(edgeFrame, theta, rho, peaks, 'FillGap', 10, 'MinLength', 10);
    
    warpedFrame = warpH(frame, obj.ipHomography, obj.warpSize);
    
    % Comparing warped edges and edges of warped frame
    warpedEdges = warpH(edgeFrame, obj.ipHomography, obj.warpSize);
    edgeWarp = edge(rgb2gray(warpedFrame), 'canny');
        
    
    figure(1); imagesc(warpedEdges)
    figure(2); imagesc(edgeWarp)
    
    %figure(2); imagesc(edgeFrame)
    %figure(3); imshow(warpedFrame)
    
    if(false)
    vertlines = [];
    for i = numel(lines):-1:1        
        if(abs(lines(i).theta - 0) < 5)
            vertlines = [vertlines, lines(i)];
        end
    end
    
    verticalLines = vertlines;
    
    % Debugging block for visualization
    debug = false;
    if(debug)
        figure(1), imshow(warpedFrame), hold on
        max_len = 0;
        for k = 1:length(lines)
           xy = [lines(k).point1; lines(k).point2];
           plot(xy(:,1),xy(:,2),'LineWidth',2,'Color','green');

           % Plot beginnings and ends of lines
           plot(xy(1,1),xy(1,2),'x','LineWidth',2,'Color','yellow');
           plot(xy(2,1),xy(2,2),'x','LineWidth',2,'Color','red');

           % Determine the endpoints of the longest line segment
           len = norm(lines(k).point1 - lines(k).point2);
           if ( len > max_len)
              max_len = len;
              xy_long = xy;
           end
        end
    end
    end
end

% Drawing the lines detected by hough transform
function debugImage = drawHoughLines(frame, lines)
    % Debug image is the frame itself to begin with
    debugImage = frame;
    
    for i = 1 :length(lines)
        
    end
end
