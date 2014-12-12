% Computing the homography useful for changing the view to a
% more central one
function computeHomography(obj)
    % Setting up the point correspondences
    % Image 1 : Standard cannonical image
    % Image 2 : Current, given image

    % Vanishing points go to each other
    % Center of the frame at the current y of vanishPt
    pts1 = [obj.imageSize(2)/2; obj.road.vanishPt(2)]; 
    pts2 = obj.road.vanishPt;

    % First extreme wrt to the border goes to bottom left
    pts1 = [pts1, [1; obj.imageSize(1)]];

    lineEq = obj.road.lanes{1}.leftEq;
    % Intercept with left border
    % Checking if within the frame
    if(lineEq(2) < obj.imageSize(1))
        pts2 = [pts2, [1; lineEq(2)]];
    else
        % If not check intercept with bottom
        bottomIntercept = -1 * lineEq(2)/lineEq(1);
        if(bottomIntercept < 0 || bottomIntercept > obj.imageSize(2))
            % Error possibly
            error('Error in finding homography');
        else
            pts2 = [pts2, [bottomIntercept; obj.imageSize(1)]];
        end
    end

    % Right extreme wrt to the border goes to bottom right
    pts1 = [pts1, [obj.imageSize(2); obj.imageSize(1)]];

    lineEq = obj.road.lanes{end}.rightEq;
    % Intercept with right border
    % Checking if within the frame
    rightIntercept = lineEq(1) * obj.imageSize(2) + lineEq(2);
    if(rightIntercept > 0 && rightIntercept < obj.imageSize(1))
        pts2 = [pts2, [obj.imageSize(2); rightIntercept]];
    else
        % If not check intercept with bottom
        bottomIntercept = -1 * lineEq(2)/lineEq(1);
        if(bottomIntercept < 0 || bottomIntercept > obj.imageSize(2))
            % Error possibly
            error('Error in finding homography');
        else
            pts2 = [pts2, [bottomIntercept; obj.imageSize(1)]];
        end
    end

    % Checking with the actual GT
    pts2(:, 2) = [5; 179];
    pts2(:, 3) = [234; 202];

    % Middle point goes to middle point
    pts1 = [pts1, mean([pts1(:, 2), pts1(:, 3)])'];
    pts2 = [pts2, mean([pts2(:, 2), pts2(:, 3)])'];

    % Compute H
    H = computeH(pts1, pts2);

    % Warp the image
    %warpedImg = warpH(image, H, obj.imageSize);
    % Display image for visualization
    %figure; imshow(image)
    %figure; imshow(warpedImg)

    obj.homography = H;
end 
