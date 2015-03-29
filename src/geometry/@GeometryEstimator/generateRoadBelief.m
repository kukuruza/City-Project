function[lanes, debugImage] = generateRoadBelief(obj, foreground, frame)
    % Function to generate the belief of the road using the foreground and
    % inverse perspective map of the road
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%%%%%%%%%%%%%%%%%%% Parameters for the method %%%%%%%%%%%%%%%%%%%%
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
    figure(2); plot(smoothBelief)
        
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
    %unionEdges = union(houghEdges, laneEdges);
    unionEdges = houghEdges;
    
    % pruning the lanes
    proxThreshold = 0.02 * imageSize(2); % Setting threshold proportionally
    %laneEdges = pruneLaneEdges(laneEdges, proxThreshold);    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Drawing the hough lines only
    %debug1 = printDebugImage(frame, obj.road.vanishPt, houghEdges, ...
    %                                    obj.ipHomography, uint8([0, 255, 0]));
    
    % Drawing the background lines
    %debug2 = printDebugImage(frame, obj.road.vanishPt, laneEdges, ...
    %                                    obj.ipHomography);
    
    %laneEdges = pruneLaneEdges(houghEdges, proxThreshold);    
    %debug3 = printDebugImage(frame, obj.road.vanishPt, laneEdges, ...
    %                                    obj.ipHomography);
    
    %obj.unionLanes = union(unionEdges, obj.unionLanes);
    %unionEdges = pruneLaneEdges(unionEdges, proxThreshold);
    
    % Getting edges from the previous frames
    debug4 = printDebugImage(frame, obj.road.vanishPt, unionEdges, ...
                                        obj.ipHomography, uint8([0, 255, 0]));
    
    %figure(1); imshow([debug1, debug2; debug3, debug4])
    figure(1); imshow(debug4)
    lanes = [];
    return
    
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
    
    % Adding the last bundle (lane)
    prunedLanes = [prunedLanes, meanBundle];
    
    RANSAC = false;
    if(RANSAC)
        % Performing RANSAC over the lines to get the best separating distance
        % Considering two points to define

        % Selecting the two points for RANSAC
        noPoints = length(prunedLanes);
        noIters = 100;
        threshold = 0.2;

        maxScore = 0;
        for i = 1:noIters
            curInd = sort(randperm(noPoints, 2));
            curDist = prunedLanes(curInd(2)) - prunedLanes(curInd(1));

            % Finding the consensus
            distances = abs((prunedLanes - prunedLanes(curInd(1))) / curDist);
            curInliers = (distances - floor(distances)) < threshold;
            curScore = sum(curInliers);

            if(curScore > maxScore)
                maxScore = curScore;
                maxInliers = curInliers;
            end
        end
        prunedLanes = prunedLanes(maxInliers);
    end
end

% Generating the debug image i.e. Drawing the lane boundaries
function debugImage = printDebugImage(frame, vanishPoint, lanePoints, ...
                                                        homography, color)
    % Setting up the color and thickness (optional argument)
    laneThickness = 2;
    if(nargin < 5)
        laneColor = uint8(reshape([255, 0, 0], [1 1 3]));
    else
        laneColor = uint8(reshape(color, [1 1 3]));
    end
    
    debugImage = frame;
    imageSize = size(frame);
    % Getting the other extreme of the road
    % Re-projecting it back to the image, for drawing the lanes
    noPoints = length(lanePoints);
    
    if isrow(lanePoints)
        imgPts = homography\ [lanePoints; ...
                        0.50 * imageSize(1) * ones(1, noPoints);...
                        ones(1, noPoints)];
    else
        imgPts = homography\ [lanePoints'; ...
                            0.50 * imageSize(1) * ones(1, noPoints);...
                            ones(1, noPoints)];
    end
    
    % Converting from homogeneous to non-homogeneous
    imgPts = [imgPts(1, :) ./ imgPts(3, :); imgPts(2, :) ./ imgPts(3, :)];
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    blankImage= zeros(size(frame, 1), size(frame, 2));
    for i = 1:size(lanePoints, 2)
        blankImage = drawLineSegment(blankImage, vanishPoint, imgPts(:, i));
    end
    blankImage = uint8(imdilate(blankImage > 0, ones(laneThickness)));
    
    debugImage = debugImage + ...
                    bsxfun(@times, blankImage, laneColor);
end