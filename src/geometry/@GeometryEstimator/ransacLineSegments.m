function [inliers, vPts] = ransacLineSegments(lines, imSize)
    % RANSAC on line segments in order to find the best vanishing point for
    % the parallel set of lines
    bestVP = [];
    
    noLines = length(lines);
    lineEq = zeros(noLines, 3);
    
    for j = 1:noLines
        %lineEq(j , :) = cross([houghLines(j).point1, 1], [houghLines(j).point2, 1]);
        %lines
        lineEq(j , :) = cross([lines(j, [1 3]), 1], [lines(j, [2 4]), 1]);
    end
    
    % Performing RANSAC
    noIters = 10000;
    distanceThreshold = 50; % 5 pixels
    %angleThreshold = 10;
    
    bestConsensus = 0;
    bestInliers = [];
    
    for j = 1:noIters
        select = randperm(noLines, 2);
        vPt = cross(lineEq(select(1), :), lineEq(select(2), :));
        % Converting into canonical form
        vPt = [vPt(1)/vPt(3), vPt(2)/vPt(3)];
        
        % Finding the intersection of other lines wrt vanishing line
        otherEq = lineEq(setdiff(1:length(lines), select), :);
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
    fprintf('RANSAC found %d / %d = %f !\n', sum(bestInliers), noLines, ...
                                                sum(bestInliers)/noLines);
    inliers = bestInliers;
    
    % Computing the pair wise intersections for all the points
    bestInliers = lines(inliers, :);
    noInliers = size(bestInliers, 1);
    %vPts = zeros(noInliers * (noInliers+1)/2, 2);
    %index = 1;
    
    %%% For now assume, the vanishing point is on the image
    % Find all the candidates lying within the image
    % Generating the pairs of lines that give rise to candidates
    [xInd, yInd] = meshgrid(1:noInliers, 1:noInliers);
    inds = [nonzeros(triu(xInd, 1)), nonzeros(triu(yInd, 1))];
    
    % Intersections
    intersects = cross(lineEq(inds(:, 1), :), lineEq(inds(:, 2), :));
    candidates = [intersects(:, 1) ./ intersects(:, 3), ...
                            intersects(:, 2) ./ intersects(:, 3)];
    
    withinImg = (candidates(:, 1) > 0) & (candidates(:, 1) < imSize(2)) & ...
                (candidates(:, 2) > 0) & (candidates(:, 2) < imSize(1));
    
    vPts = candidates(withinImg, :);
    size(vPts)
    return
%     for j = 1:noInliers
%         for k = j+1:noInliers
%             % Each line must be from the different half of the image
%             %if((bestInliers(j, 1) - 0.5 * imSize(2)) * ...
%             %                (bestInliers(k, 1) - 0.5 * imSize(2)) < 0)
%                 point = cross(lineEq(j, :), lineEq(k, :));
%                 
%                 % Ignore if its ill-conditioned
%                 point2D = [point(1)/(point(3) + 1e-4) , ...
%                                     point(2)/(point(3) + 1e-4)];
%                 
%                 if(sum(point2D < )
%                     vPts(index, :) = point2D;
%                     index = index + 1;
%                 end
%         end
%     end
%         end
%     end
% 
% vPts = vPts(1:index-1, :);
end