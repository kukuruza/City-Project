function[debugFrame, lanes] = generateRoadBelief(obj, foreground, frame)
    % Function to generate the belief of the road using the foreground
    
    % Computing the inverse perspective transform, for the first time
    laneRatio = 0.3;
    laneWidth = obj.imageSize(2) * 0.25;
    [ipHomography, warpedBackground] = obj.computeIPTransform(foreground, laneRatio, laneWidth); 
    
    % Valid range for histogram
    minCol = obj.imageSize(2)/2 - laneWidth;
    maxCol = obj.imageSize(2)/2 + laneWidth;
    
    warpedBackground = warpedBackground(:, minCol:maxCol);
    
    % Check if roadBelief has been initiated
    if(size(obj.roadBelief, 1) > 0)
        obj.roadBelief = obj.roadBelief + sum(warpedBackground); 
    else
        obj.roadBelief = sum(warpedBackground); 
    end
    
    % Smoothen the belief and estimate the number of minima
    windowSize = 10;
    normBelief = obj.roadBelief ./ sum(obj.roadBelief);
    smoothBelief = smooth(normBelief, windowSize)'; % Make it a row vector
    
    % Finding the points of minima based on being a local minima
    minimaRange = 15;
    localMinima = colfilt(smoothBelief, [1, minimaRange], 'sliding', @min);
    
    % Removing the zero pad in the beginning and the end
    compareRange = (minimaRange+1):(length(localMinima)-minimaRange);
    localMinima = localMinima(compareRange) == smoothBelief(compareRange);
    
    % Finding transitions and locations of lane edges
    transitions = [0, ...
       ((localMinima(2:end-1) ~= localMinima(1:end-2))|(localMinima(2:end-1) ~= localMinima(3:end))) ...
       & localMinima(2:end-1), ...
                   0];
               
    % Adding all the offsets
    laneEdges = find(transitions == 1) + minimaRange + minCol;
                
    % Re-projecting it back to the image, for drawing the lanes
    imgPts = ipHomography \ [laneEdges; ...
                            obj.imageSize(1) * ones(1, length(laneEdges));...
                            ones(1, length(laneEdges))];
    
    % Converting from homogeneous to non-homogeneous
    imgPts = [imgPts(1, :) ./ imgPts(3, :); imgPts(2, :) ./ imgPts(3, :)]; 
    
    lanes = zeros(size(imgPts));
    % Creating the equations for the lanes
    for i = 1:length(imgPts)    
        lanes(1, i) = (imgPts(2, i) - obj.road.vanishPt(2)) /...
                        (imgPts(1, i) - obj.road.vanishPt(1));
        lanes(2, i) = obj.road.vanishPt(2) - lanes(1, i) * obj.road.vanishPt(1);
    end
    
    debugFrame = frame;
    % Drawing the points on the image
    for i = 1:size(imgPts, 2)
        debugFrame = drawLineSegment(debugFrame, obj.road.vanishPt, imgPts(:, i));
    end
    
    debug = false;
    if(debug)
        % Warping the frame for debugging
        warpedFrame = warpH(frame, ipHomography, size(frame));
    
        % Getting the edge image and hough transformation
        grayFrame = rgb2gray(warpedFrame);
        edgeFrame = edge(grayFrame, 'canny');
        [houghFrame, theta, rho] = hough(edgeFrame);
        
        % Detecting the lines
        peaks = houghpeaks(houghFrame, 20);
        lines = houghlines(edgeFrame, theta, rho, peaks, 'FillGap', 1, 'MinLength', 1);
         
        figure, imshow(warpedFrame), hold on

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
        
        %figure(3); imshow(debugFrame)
        %figure(4); plot(smoothBelief)
        %figure(5); imshow(warpedFrame)
        %figure(6); imshow(grayFrame)
        %figure(6); imagesc(houghFrame)
    end
end
