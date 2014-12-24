function[vanishPoint, boundaryLanes] = estimateRoad(frame, binaryImgPath, noFrames)
    % Reading the binary images from the path, reading the vanishing point
    % and boundary lanes, taking an average / RANSAC estimate for better
    % estimate

    % Reading the file if non-empty
    imagePaths = dir(fullfile(binaryImgPath, '*.jpg'));
    noImages = min(numel(imagePaths), noFrames);
    
    if(noImages == 0)
       error('Binary image path empty in estimateRoad(.)');
    end

    vanishPoint = zeros(noImages, 2);
    leftBoundary = zeros(noImages, 1); 
    rightBoundary = zeros(noImages, 1); 

    for i = 1:noImages
       image = imread(fullfile(binaryImgPath, imagePaths(i).name));
       image = imresize(image, [size(frame, 1), size(frame, 2)]);

       % Read the vanishing point
       % first maxima in transformed
       transposeImg = image';
       [~, maxLinearId] = max(transposeImg(:));
       [xPt, yPt] = ind2sub(size(image'), maxLinearId);
       vanishPoint(i, :) = [xPt, yPt];

       % Reading the extremes
       % Sampling at few points from vanishPoint
       ySamples = (yPt + 5) : 1 : (yPt + 50); 
       [~, xSamplesLeft] = max(image(ySamples, :), [], 2);
       [~, xSamplesRight] = max(fliplr(image(ySamples, :)), [], 2);
       xSamplesRight = size(image, 2) + 1 - xSamplesRight;

       % Linear fit to get the left extreme and right extreme
       leftExt = polyfit(xSamplesLeft', ySamples, 1); 
       rightExt = polyfit(xSamplesRight', ySamples, 1);

       % Stacking left and right angles for lanes
       leftBoundary(i) = atan(leftExt(1)) * 180 / pi;
       rightBoundary(i) = atan(rightExt(1)) * 180 / pi;
    end
    
    % Performing RANSAC selection to get the best vanishing point and
    % extremes
   
    % VanishingPt RANSAC
    maxNoInliers = 0;
    distanceThreshold = 10; % 10 pixels
    for i = 1:noImages
        inliers = hypot(vanishPoint(:, 1) - vanishPoint(i, 1), ...
                    vanishPoint(:, 2) - vanishPoint(i, 2)) < distanceThreshold;
        noInliers = sum(inliers);
        
        if(noInliers > maxNoInliers)
           maxNoInliers = noInliers;
           maxInliers = inliers;
        end
    end    
    vanishPoint = mean(vanishPoint(maxInliers, :));
    
    % Left Extreme RANSAC
    maxNoInliers = 0;
    angleThreshold = 5; % 5 degrees
    for i = 1:noImages
        inliers = abs(leftBoundary - leftBoundary(i)) < angleThreshold;
        noInliers = sum(inliers);
        
        if(noInliers > maxNoInliers)
           maxNoInliers = noInliers;
           maxInliers = inliers;
        end
    end
    leftBoundary = mean(leftBoundary(maxInliers));
   
    % RightExtreme RANSAC
    maxNoInliers = 0;
    for i = 1:noImages
        inliers = abs(rightBoundary - rightBoundary(i)) < angleThreshold;
        noInliers = sum(inliers);
        
        if(noInliers > maxNoInliers)
           maxNoInliers = noInliers;
           maxInliers = inliers;
        end
    end  
    rightBoundary = mean(rightBoundary(maxInliers));
    
    boundaryLanes = [leftBoundary, rightBoundary];
    
    % Debug, draw on the frame for display
    debug = false;
    if(debug)
        % Draw the vanishingpoint
        redColor = uint8([255 0 0]);  % [R G B]; class of red must match class of I
        vpMarker = vision.MarkerInserter('Shape','Circle', 'Fill', true, ...
            'Size', 5, 'FillColor','Custom','CustomFillColor',redColor, 'Opacity', 0.9);
        debugImg = step(vpMarker, frame, uint32(vanishPoint)');
        
        % Drawing the left boundary
        % Checking if it intercepts left frame or bottom frame
        m = tand(leftBoundary); % Slope of the line
        leftIntercept = m + vanishPoint(2) - m * vanishPoint(1);
        if(leftIntercept < size(frame, 1))
            debugImg = drawLineSegment(debugImg, vanishPoint, [1, leftIntercept]);
        else
            % Checking for the bottom intercept 
            bottomIntercept = (size(frame, 1) - vanishPoint(2) + m*vanishPoint(1))...
                            / m;
            debugImg = drawLineSegment(debugImg, vanishPoint, ...
                                        [bottomIntercept, size(frame, 1)]);
        end
        
        % Drawing the right boundary
        % Checking if it intercepts left frame or bottom frame
        m = tand(rightBoundary); % Slope of the line
        rightIntercept = m * size(frame, 2) + vanishPoint(2) - m * vanishPoint(1);
        if(leftIntercept < size(frame, 1))
            debugImg = drawLineSegment(debugImg, vanishPoint, ...
                                        [size(frame, 2), rightIntercept]);
        else
            % Checking for the bottom intercept 
            bottomIntercept = (size(frame, 1) - vanishPoint(2) + m*vanishPoint(1))...
                            / m;
            debugImg = drawLineSegment(debugImg, vanishPoint, ...
                                        [bottomIntercept, size(frame, 1)]);
        end
        
        figure; imshow(debugImg)
    end
end