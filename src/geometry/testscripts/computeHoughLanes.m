function [ verticalLines ] = computeHoughLanes(warpedFrame)
    % Function to generate the lanes using hough transform
    % 
    % Usage:
    % computeHoughLanes();
    
    % Getting the edge image and hough transformation
    grayFrame = rgb2gray(warpedFrame);
    edgeFrame = edge(grayFrame, 'canny');
    [houghFrame, theta, rho] = hough(edgeFrame);
    
    % Vertical lines are only to be considered
    % Detecting the lines
    peaks = houghpeaks(houghFrame, 20);
    lines = houghlines(edgeFrame, theta, rho, peaks, 'FillGap', 10, 'MinLength', 10);
    
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