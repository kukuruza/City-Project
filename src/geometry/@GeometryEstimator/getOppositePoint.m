% Get the corresponding point using homography error
function[oppositePt] = getOppositePoint(obj, point, line, oppLine)
    % This method assumes the presence of two extreme for the road,
    % gets the opposite point on the other side of cannonical
    % road, for a given point. 
    % Uses homography and projects it back to get error for the
    % best fit
    %
    % Usage: 
    % oppositePt=geometryObject.getOppositePoint(point,line,oppLine);
    %

    % Collect points in pts1 and pts2 for homography computation
    % Vanishing points go to each other
    % Center of the frame at the current y of vanishPt
    pts1 = [obj.imageSize(2)/2; obj.road.vanishPt(2)];
    pts1 = [pts1, [1; obj.imageSize(1)]];
    pts1 = [pts1, [obj.imageSize(2); obj.imageSize(1)]];
    pts1 = [pts1, mean([pts1(:, 2), pts1(:, 3)])'];
    pts2 = obj.road.vanishPt;
    
    % Find the exact point closest to the line
    %closePtX = (line(1) * (point(2) - line(2)) + point(1)) / (1 + line(1)^2);
    %closePt = [closePtX; closePtX * line(1) + line(2)];
    
    % Generate points on the both lines
    yArgs = floor(obj.road.vanishPt(2)):(2*obj.imageSize(2)-obj.road.vanishPt(2));
    linePts = [ (yArgs - line(2)) / line(1); yArgs];
    oppLinePts = [ (yArgs - oppLine(2)) / oppLine(1); yArgs];
    
    % Range of points to check for homography agreement
    argRange = -10:2:10;
    
    % Fix the set of points against which we test
    curPtInd = find(point(2) == linePts(2, :));
    curPtInd = curPtInd(1);
    testPts2 = linePts(:, curPtInd + (argRange));
    
    % Range of values
    maxRange = 50;
    indexRange = curPtInd + (-maxRange:maxRange);
    
    sqError = inf(1, length(indexRange));
    
    % Iterating over the points on opposite line, near the equal y
    % coordinate point
    for curPtInd = indexRange
        guessPt = oppLinePts(:, curPtInd);
        iterPts2 = [pts2, guessPt, point, mean([guessPt, point], 1)'];
        
        % Compute homography and check for error
        iterH = computeH(pts1, iterPts2);
        
        % Points for which we need to check for homograhy (+- 5 around
        % guessPtInd)
        testPts1 = oppLinePts(:, curPtInd + (argRange));
        estPts1 = iterH * [testPts1; ones(1, size(testPts1, 2))];
        estPts1 = estPts1(1:2, :) ./ repmat(estPts1(3, :), [2, 1]);
        
        estPts2 = iterH * [testPts2; ones(1, size(testPts2, 2))];
        estPts2 = estPts2(1:2, :) ./ repmat(estPts2(3, :), [2, 1]);
        
        sqError(curPtInd-min(indexRange)+1) = sum(abs(estPts1(2, :) - estPts2(2, :)));
    end
    
    figure; plot(sqError)
    
    oppositePt = [];
    return
    [minVal, minId] = min(sqError);

    minId = find(point(2) == oppLinePts(2,:));
    guessPt = oppLinePts(:, minId);
    iterPts2 = [pts2, guessPt, point, mean([guessPt, point], 1)'];

    % Compute homography and check for error
    H = computeH(pts1, iterPts2);
    oppositePt = H;
    %guessPt = [(closePt(2) - oppLine(2)) / oppLine(1); closePt(2)];
    
    % Compute homography with point
    
    
    %
    
    % Best fit oppositve point for the given point
    %oppositePt = [];
end

%function getPointsa