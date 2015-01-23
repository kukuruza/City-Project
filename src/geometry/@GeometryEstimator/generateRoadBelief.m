function[lanes, debugImage] = generateRoadBelief(obj, foreground, frame)
    % Function to generate the belief of the road using the foreground and
    % inverse perspective map of the road
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%% Parameters for the method
    imageSize = size(frame);
    laneRatio = 0.5;
    laneWidth = imageSize(2) * 0.25;
    
    % Smoothing kernel size
    windowSize = 7;
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
    minCol = obj.imageSize(2)/2 - laneWidth;
    maxCol = obj.imageSize(2)/2 + laneWidth;
    
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
       ((localMinima(2:end-1) ~= localMinima(1:end-2))|(localMinima(2:end-1) ~= localMinima(3:end))) ...
       & localMinima(2:end-1), ...
                   0];
               
    % Adding all the offsets
    laneEdges = find(transitions == 1) + minimaRange + minCol;
    
    % Re-projecting it back to the image, for drawing the lanes
    imgPts = obj.ipHomography \ [laneEdges; ...
                            %size(warpedBackground, 1) * ones(1, length(laneEdges));...
                            0.90 * obj.imageSize(1) * ones(1, length(laneEdges));...
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
    
    debug = false;
    if(debug) 
        debugImage = printDebugImage(frame, obj.road.vanishPt, imgPts);
    else 
        debugImage = frame;
    end
end

% Generating the debug image i.e. Drawing the lane boundaries
function debugImage = printDebugImage(frame, vanishPoint, lanePoints)
    debugImage = frame;
    % Setting up the color and thickness
    laneThickness = 1;
    laneColor = uint8(reshape([255, 0, 0], [1 1 3]));
    
    blankImage= zeros(size(frame, 1), size(frame, 2));
    for i = 1:size(lanePoints, 2)
        blankImage = drawLineSegment(blankImage, vanishPoint, lanePoints(:, i));
    end
    blankImage = uint8(imdilate(blankImage > 0, ones(laneThickness)));
    
    debugImage = debugImage + ...
                    bsxfun(@times, blankImage, laneColor); 
end