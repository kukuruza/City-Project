function[lanes, debugImage] = generateRoadBelief(obj, foreground, frame)
    % Function to generate the belief of the road using the foreground and
    % inverse perspective map of the road
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Parameters for the method
    imageSize = size(frame);
    laneRatio = 0.25;
    laneWidth = imageSize(2) * 0.3;
    
    % Smoothing kernel size
    windowSize = 15;
    % Minima window size
    minimaRange = 5;
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Computing the inverse perspective transform, for the first time
    if(isempty(obj.warpSize))
        obj.ipHomography = obj.computeIPTransform(foreground, laneRatio, laneWidth); 

        % Find the tight fit warp size ( first time, use a large row size)
        warpedFrame = warpH(frame, obj.ipHomography, ...
                            [3*laneRatio, 1.0, 1.0] .* size(frame));
                        
        background = sum(warpedFrame, 3) == 0;
        [~, maxRowSize] = max(sum(background, 2));
        obj.warpSize = [maxRowSize, size(frame, 2), size(frame, 3)];
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    % Valid range for histogram
    minCol = floor(obj.imageSize(2)/2 - laneWidth);
    maxCol = floor(obj.imageSize(2)/2 + laneWidth);
    
    % Warping the foreground
    warpedBackground = warpH(foreground, obj.ipHomography, obj.warpSize);
    warpedBackground = warpedBackground(:, minCol:maxCol);
    
    % Check if roadBelief has been initiated
    if(size(obj.roadBelief, 1) > 0)
        obj.roadBelief = obj.roadBelief + sum(warpedBackground); 
    else
        obj.roadBelief = sum(warpedBackground); 
    end
    
    % Smoothen the belief and estimate the number of minima
    normBelief = obj.roadBelief ./ sum(obj.roadBelief);
    smoothBelief = smooth(normBelief, windowSize)'; % Make it a row vector
    
    % Finding the points of minima based on being a local minima
    localMinima = colfilt(smoothBelief, [1, minimaRange], 'sliding', @min);
    
    % Removing the zero pad in the beginning and the end
    compareRange = (minimaRange+1):(length(localMinima)-minimaRange);
    localMinima = localMinima(compareRange) == smoothBelief(compareRange);
    
    % Finding transitions and locations of lane edges
    transitions = [0, ...
       ((localMinima(2:end-1) ~= localMinima(1:end-2))|...
       (localMinima(2:end-1) ~= localMinima(3:end))) ...
       & localMinima(2:end-1), ...
                   0];
               
    % Adding all the offsets
    laneEdges = find(transitions == 1) + minimaRange + minCol;
    
    % Getting the points using hough transform
    houghEdges = obj.computeHoughLanes(frame);
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Taking the best out of both the hough and already present edges
    laneEdges = union(houghEdges, laneEdges);
    
    % pruning the lanes
    proxThreshold = 0.01 * imageSize(2); % Setting threshold proportionally
    laneEdges = pruneLaneEdges(laneEdges, proxThreshold);    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    % Re-projecting it back to the image, for drawing the lanes
    imgPts = obj.ipHomography\ [laneEdges; ...
                    %size(warpedBackground, 1) * ones(1, length(laneEdges));...
                    0.50 * imageSize(1) * ones(1, length(laneEdges));...
                    ones(1, length(laneEdges))];

    % Showing the warped background
    %figure(2); imshow([reImg, frame])
    %figure(2); imshow(warpH(frame, obj.ipHomography, obj.warpSize))
    %figure(3); plot(smoothBelief)
    
    % Converting from homogeneous to non-homogeneous
    imgPts = [imgPts(1, :) ./ imgPts(3, :); imgPts(2, :) ./ imgPts(3, :)]; 
    noPts = size(imgPts, 2);
    lanes = zeros(size(imgPts));
    % Creating the equations for the lanes
    for i = 1:noPts
        lanes(1, i) = (imgPts(2, i) - obj.road.vanishPt(2)) /...
                        (imgPts(1, i) - obj.road.vanishPt(1));
        lanes(2, i) = obj.road.vanishPt(2) - lanes(1, i) * obj.road.vanishPt(1);
    end
    
    debug = true;
    if(debug) 
        debugImage = printDebugImage(frame, obj.road.vanishPt, imgPts);
    else 
        debugImage = frame;
    end
    
    figure(1); imshow(debugImage)
end

% Pruning the edges for consensus
function prunedLanes = pruneLaneEdges(laneEdges, proxThreshold)
    % Setting the default values for proximal threshold
    if(nargin < 2)
        % Default of 5 pixels
        proxThreshold = 5;
    end
    
    % Do nothing, return
    if(length(laneEdges) < 2)
        prunedLanes = laneEdges;
        return
    end
    
    prunedLanes = [];
    % Sum and number of members in the current bundle
    sumBundle = laneEdges(1); noBundle = 1; meanBundle = laneEdges(1);
    for i = 2:length(laneEdges)
        % If close, merge into the bundle
        %if(abs(laneEdges(i)-meanBundle) <= proxThreshold)
        if(abs(laneEdges(i)-meanBundle) <= proxThreshold)
            sumBundle = sumBundle + laneEdges(i);
            noBundle = noBundle + 1;
            meanBundle = sumBundle / noBundle;
        else
            prunedLanes = [prunedLanes, meanBundle];
            sumBundle = laneEdges(i); noBundle = 1;
            meanBundle = laneEdges(i);
        end
    end
    
    % Performing RANSAC over the lines to get the best separating distance
    % Considering two points to define
    
end

% Generating the debug image i.e. Drawing the lane boundaries
function debugImage = printDebugImage(frame, vanishPoint, lanePoints, laneColor)
    debugImage = frame;
    
    % Setting up the color and thickness
    if(nargin < 4)
        laneColor = uint8(reshape([255, 0, 0], [1 1 3]));
    end
    laneThickness = 2;
    
    blankImage= zeros(size(frame, 1), size(frame, 2));
    for i = 1:size(lanePoints, 2)
        blankImage = drawLineSegment(blankImage, vanishPoint, lanePoints(:, i));
    end
    blankImage = uint8(imdilate(blankImage > 0, ones(laneThickness)));
    
    debugImage = debugImage + ...
                    bsxfun(@times, blankImage, laneColor); 
end