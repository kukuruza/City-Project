function generateRoadBelief(obj, foreground)
    % Function to generate the belief of the road using the foreground
    
    % Computing the inverse perspective transform, for the first time
    laneRatio = 0.3;
    laneWidth = obj.imageSize(2) * 0.25;
    [~, warpedFrame] = obj.computeIPTransform(foreground, laneRatio, laneWidth);
    
    % Valid range for histogram
    minCol = obj.imageSize(2)/2 - laneWidth;
    maxCol = obj.imageSize(2)/2 + laneWidth;
    
    warpedFrame = warpedFrame(:, minCol:maxCol);
    
    % Check if roadBelief has been initiated
    if(size(obj.roadBelief, 1) > 0)
        obj.roadBelief = obj.roadBelief + sum(warpedFrame); 
    else
        obj.roadBelief = sum(warpedFrame); 
    end
    
    % Smoothen the belief and estimate the number of minima
    normBelief = obj.roadBelief ./ sum(obj.roadBelief);
    smoothBelief = smoothts(normBelief, 'g', 40);
    
    figure(2); plot(smoothBelief)
    
end