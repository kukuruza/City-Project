function [grouping, bestH]  = ransacHomography(pts1, pts2, type)
    % Function to identify the components of two planes using matchines
    % 
    % Uses homography to identify points
    % We restrict the type of homography that can be used by setting the
    % type parameter
    %
    % 'general'(default)-Refers to a 3 x 3 homography without any constraints 
    % 'translation' - Refers to just a translation homography between the image pts 
    
    if(nargin < 3)
        type = 'general';
    end
    
    assert(size(pts1, 1) == 2)
    assert(size(pts2, 1) == 2)
    
    % Homography computation needs 8 variables ie 4 points
    noPts = size(pts1, 2);
    maxIters = 200;
    threshold = 0.5; % 5 pixel threshold for H inlier check
    
    % Best consensus
    bestCons = 0;
    bestInliers = [];
    
    switch type
        case 'general'
            % RANSAC for the best plane
            for i = 1:maxIters
                randPts = randperm(noPts, 4);

                % Computing H
                H = computeH(pts1(:, randPts)', pts2(:, randPts)');

                % Checking for inliers
                estPts = H * [pts2; ones(1, noPts)];
                %inliers = rms([estPts(1, :)./estPts(3, :); estPts(2, :)./estPts(3, :)]  - pts1) < threshold;

                % L1 norm is faster
                inliers = sum(abs([estPts(1, :)./estPts(3, :); estPts(2, :)./estPts(3, :)]  - pts1)) ...
                                                        < threshold;
                
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
    
        case 'translation'
            % RANSAC for the best plane
            for i = 1:min(maxIters, noPts)
                randPt = randi(noPts);

                % Computing the translation
                translation = pts1(:, randPt) - pts2(:, randPt);
                
                movedPts1 = bsxfun(@plus, pts2, translation);
                inliers = sum(abs(movedPts1 - pts1)) < threshold;
                
                if(sum(inliers) > bestCons)
                    % Update the best consensus
                    bestCons = sum(inliers);
                    bestInliers = inliers;
                    bestH = translation;
                end
            end

            % Printing the message
            %fprintf('Consensus of %f with %d/%d points found!\n', bestCons/noPts, bestCons, noPts);

            % Assign the inlier points one plane
            bestH = eye(3);
            bestH(1:2, 3) = translation;
            grouping = bestInliers;
    end
end


