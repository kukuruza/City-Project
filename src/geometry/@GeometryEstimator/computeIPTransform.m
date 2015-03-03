function ipHomography  = computeIPTransform(obj, image, laneRatio, laneWidth)
    % Finding the homography for an approximate inverse perspective 
    % transformation
    % 
    % Usage: 
    % homography
    %   = geometryEstimator.computeIPTransform(image, laneRatio, laneWidth)
    % 
    % laneWidth defines the extent to which the end point is close to 
    % vanishing point (default 0.50)
    % Lanewidth defines the width of the lane after inverse perspective
    %   default 0.25 * no of columns
    
    % Setting up the point correspondences
    % Image 1 : Inverse perspective image
    % Image 2 : Current, given image
    
    %
    % Checking for arguments and initializng them with defaults otherwise
    imageSize = size(image);
    if(nargin < 4)
        %laneWidth = 200;
        laneWidth = imageSize(2) * 0.25;
    end
    
    if(nargin < 3)
       laneRatio = 0.50; 
    end
    
    % Vanishing points go to each other
    % Center of the frame at the current y of vanishPt
    % pts1 = [imageSize(2)/2; obj.road.vanishPt(2)]; 
    % pts2 = obj.road.vanishPt;

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % First extreme wrt to the border goes to bottom left
    pts1 = []; pts2 = [];
    pts1 = [pts1, [imageSize(2)/2 - laneWidth; imageSize(1)]];
    
    % Using the automatically detected left lanes
    slope = tand(obj.boundaryLanes(1));
    lineEq = [slope, obj.road.vanishPt(2) - slope * obj.road.vanishPt(1)];
    
    %lineEq = obj.road.lanes{1}.leftEq;
    % Intercept with left border
    % Checking if within the frame
    if(lineEq(2) < imageSize(1))
        pts2 = [pts2, [1; lineEq(2)]];
    else
        % If not, check intercept with bottom
        bottomIntercept = -1 * lineEq(2)/lineEq(1);
        [bottomIntercept, imageSize(2)]
        if(bottomIntercept < 0 || bottomIntercept > imageSize(2))
            % Error possibly
            error('Error in finding homography');
        else
            pts2 = [pts2, [bottomIntercept; imageSize(1)]];
        end
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Right extreme wrt to the border goes to bottom right
    pts1 = [pts1, [imageSize(2)/2 + laneWidth; imageSize(1)]];

    % Using the automatically detected left lanes
    slope = tand(obj.boundaryLanes(2));
    lineEq = [slope, obj.road.vanishPt(2) - slope * obj.road.vanishPt(1)];
    
    %lineEq = obj.road.lanes{end}.rightEq;
    % Intercept with right border
    % Checking if within the frame
    rightIntercept = lineEq(1) * imageSize(2) + lineEq(2);
    if(rightIntercept > 0 && rightIntercept < imageSize(1))
        pts2 = [pts2, [imageSize(2); rightIntercept]];
    else
        % If not check intercept with bottom
        bottomIntercept = -1 * lineEq(2)/lineEq(1);
        if(bottomIntercept < 0 || bottomIntercept > imageSize(2))
            % Error possibly
            error('Error in finding homography');
        else
            pts2 = [pts2, [bottomIntercept; imageSize(1)]];
        end
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Points on the lane go to the other extreme of the image (top)
    pts2 = [pts2, [pts2(:, 1) * (1-laneRatio) + obj.road.vanishPt * laneRatio]];
    pts1 = [pts1, [imageSize(2)/2 - laneWidth; 10]];
    
    pts2 = [pts2, [pts2(:, 2) * (1-laneRatio) + obj.road.vanishPt * laneRatio]];
    pts1 = [pts1, [imageSize(2)/2 + laneWidth; 10]];
    
    % Reducing the image height based on the lane ratio
    pts1(2, 1:2) = floor(pts1(2, 1:2) * laneRatio);
    
    % Compute H
    ipHomography = computeH(pts1, pts2);
    %obj.homography = H;
end