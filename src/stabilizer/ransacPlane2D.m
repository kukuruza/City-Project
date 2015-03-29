function [grouping, bestH]  = ransacPlane2D(pts1, pts2)
    % Function to identify the components of two planes using matchines
    % 
    % Uses homography to identify points
    
    % Homography computation needs 8 variables ie 4 points
    noPts = size(pts1, 2);
    maxIters = 200;
    threshold = 1; % 5 pixel threshold for H inlier check
    
    % Best consensus
    bestCons = 0;
    bestInliers = [];
    
    % RANSAC for the best plane
    for i = 1:maxIters
        randPts = randperm(noPts, 4);
        
        % Computing H
        H = computeH(pts1(:, randPts)', pts2(:, randPts)');
        
        % Checking for inliers
        estPts = H * [pts2; ones(1, noPts)];
        inliers = rms([estPts(1, :)./estPts(3, :); estPts(2, :)./estPts(3, :)]  - pts1) < threshold;
        
        if(sum(inliers) > bestCons)
            % Update the best consensus
            bestCons = sum(inliers);
            bestInliers = inliers;
            bestH = H;
        end
    end
    
    % Printing the message
    %fprintf('Consensus of %f with %d/%d points found!\n', bestCons/noPts, bestCons, noPts);
    
    % Assign the inlier points one plane
    grouping = bestInliers;
end


