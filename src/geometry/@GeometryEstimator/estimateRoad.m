function[vanishPoint, boundaryLanes, regionMask] = estimateRoad(frame, binaryImgPath, noFrames)
    % Reading the binary images from the path, reading the vanishing point
    % and boundary lanes, taking an average / RANSAC estimate for better
    % estimate

    % Reading the file if non-empty
    imagePaths = dir(fullfile(binaryImgPath, '*.jpg'));
    if(numel(imagePaths) == 0)
        imagePaths = dir(fullfile(binaryImgPath, '*.png'));
    end
    noImages = min(numel(imagePaths), noFrames);
    
    if(noImages == 0)
       error('Binary image path empty in estimateRoad(.)');
    end

    % Pre-setting the outputs to avoid errors
    vanishPoint = zeros(noImages, 2);
    leftBoundary = zeros(noImages, 1); 
    rightBoundary = zeros(noImages, 1); 
    mask = zeros(size(frame, 1), size(frame, 2));
    
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
    debug = true;
    if(debug)
        [~, regionMask] = printDebugImage(frame, vanishPoint, leftBoundary,...
                                                            rightBoundary);
    end
end

% Generating the debug image i.e. Drawing the roads and road extent on the
% frame
function [debugImage, regionMask] = printDebugImage(frame, vanishPoint, ...
                        leftBoundary, rightBoundary)
        % What all to draw on the debug image (in the below order)
        drawRegion = true;
        drawBoundaries = true;
        drawVanishPoint = true;
        
        % Properties
        patchColor = [40, 40, 40]; % Highlighting the patch of road
        roadThickness = 5;  % thickness of the road ( dilating kernel size)
        roadColor = [0 0 255]; % color of the lanes of the boundary
        
        % Pre-defining to avoid break down
        debugImage = frame;
        imageSize = size(frame);
        regionMask = uint8(zeros(size(frame)));
        
        % Draw the vanishingpoint
        greenColor = uint8([0 240 0]);  % [R G B]; class of red must match class of I
        vpMarker = vision.MarkerInserter('Shape','Circle', 'Fill', true, ...
            'Size', 10, 'FillColor','Custom','CustomFillColor',greenColor, 'Opacity', 1.0);
        
        
        % Finding the extremes of the right and left images
        extremes = zeros(2, 4);
        % Checking if it intercepts left frame or bottom frame
        m = tand(leftBoundary); % Slope of the line
        % Replacing 90 deg slope with 89 / -90 with -89
        if(abs(m) > 100) 
            m = sign(m) * 100; 
        end
        
        leftIntercept = m + vanishPoint(2) - m * vanishPoint(1);
        if(leftIntercept < imageSize(1))
            extremes(1, :) = [vanishPoint, 1, leftIntercept];
        else
            % Checking for the bottom intercept 
            bottomIntercept = (imageSize(1) - vanishPoint(2) + m*vanishPoint(1))...
                            / m;
            extremes(2, :) = [vanishPoint, bottomIntercept, imageSize(1)];
        end
        
        % Checking if right intercepts left frame or bottom frame
        m = tand(rightBoundary); % Slope of the line
        % Replacing 90 deg slope with 89 / -90 with -89
        if(abs(m) > 100)
            m = sign(m) * 100;
        end
        
        rightIntercept = m * imageSize(2) + vanishPoint(2) - m * vanishPoint(1);
        if(rightIntercept < imageSize(1))
            extremes(2, :) = [vanishPoint, imageSize(2), rightIntercept];
        else
            % Checking for the bottom intercept 
            bottomIntercept = (imageSize(1) - vanishPoint(2) + m*vanishPoint(1))...
                            / m;
            extremes(2, :) = [vanishPoint, bottomIntercept, imageSize(1)];
        end
        
        % Computing the regionMask
        regionMask = drawLineSegment(regionMask, extremes(1, 1:2), extremes(1, 3:4));
        regionMask = drawLineSegment(regionMask, extremes(2, 1:2), extremes(2, 3:4));
        
        % Detecting the boundaries and applying a white transparent shade
        [~, startCol]= max(regionMask, [], 2);

        % Flipping and finding the other end of the max
        flipped = flip(regionMask, 2);
        [~, endCol] = max(flipped, [], 2);
        
        % Adjusting the end column
        endCol = size(frame, 2) + 1 - endCol;
        
        regionMask = zeros(imageSize(1:2));
        leftAll = false;
        rightAll = false;
        for i = uint32(vanishPoint(2)):imageSize(1)
            % Road must diverge
            if(abs(endCol(i) - startCol(i)) < 5 && ...
                (leftAll && rightAll) == false && ...
                i > vanishPoint(2) + 30)
                % Checking if the end points reached frame ends
                if(startCol(i) > size(frame, 2)/2)
                    leftAll = true;
                end
                if(endCol(i) < size(frame, 2)/2)
                    rightAll = true;
                end
            end
            
            if(leftAll) 
                startCol(i) = 1; 
            end
            if(rightAll)
                endCol(i) = size(frame, 2); 
            end
           
            regionMask(i, startCol(i) : endCol(i)) = 1;
        end
        
        % Drawing the region with white patch
        if(drawRegion)
            debugImage = debugImage + ...
                    bsxfun(@times, regionMask(:, :, [1 1 1]), patchColor);  
        end
        
        % Drawing the boundaries
        if(drawBoundaries)
            % Thickness of the boundary lines
            boundaryImage = imdilate(regionMask >0, ones(roadThickness));
            debugImage = debugImage + ...
                    bsxfun(@times, boundaryImage(:, :, [1 1 1]), roadColor); 
        end
        
        % Drawing the vanishing point
        if(drawVanishPoint)
            debugImage = step(vpMarker, debugImage, uint32(vanishPoint));
        end
end