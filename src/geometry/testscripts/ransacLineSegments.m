function [inliers, bestVP] = ransacLineSegments(houghLines)
    % RANSAC on line segments in order to find the best vanishing point for
    % the parallel set of lines
    bestVP = [];
    inliers = [];
   
    noLines = length(houghLines);
    lineEq = zeros(noLines, 3);
    for j = 1:noLines
        lineEq(j , :) = cross([houghLines(j).point1, 1], [houghLines(j).point2, 1]);
    end
    
    % Performing RANSAC
    noIters = 10000;
    distanceThreshold = 50; % 5 pixels
    
    bestConsensus = 0;
    bestInliers = [];
    
    tic
    for j = 1:noIters
        select = randperm(noLines, 2);
        vPt = cross(lineEq(select(1), :), lineEq(select(2), :));
        % Converting into canonical form
        vPt = [vPt(1)/vPt(3), vPt(2)/vPt(3)];
        
        % Finding the intersection of other lines wrt vanishing line
        otherEq = lineEq(setdiff(1:length(houghLines), select), :);
        vLine = [0 1 -vPt(2)];
        intersect = cross(otherEq, repmat(vLine, [noLines - 2, 1]));
        intersect = [intersect(:, 1) ./ intersect(:, 3), ...
                                    intersect(:, 2) ./ intersect(:, 3)]; 
                                
        inliers = abs(intersect(:, 1) - vPt(1)) < distanceThreshold;
        consensus = sum(inliers);
        
        if(consensus > bestConsensus)
            bestInliers = inliers;
        end
    end
    fprintf('RANSAC found %d / %d = %f !', sum(bestInliers), noLines, ...
                                                sum(bestInliers)/noLines);
    inliers = bestInliers;
end

