function[vanishPoint, boundaryLanes, mask] = estimateRoad(frame, binaryImgPath, noFrames)
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
    debugImg = frame;
    
    if(debug)
        % Draw the vanishingpoint
        redColor = uint8([220 0 0]);  % [R G B]; class of red must match class of I
        yellowColor = uint8([255 255 0]);  % [R G B]; class of red must match class of I
        greenColor = uint8([0 240 0]);  % [R G B]; class of red must match class of I
        vpMarker = vision.MarkerInserter('Shape','Circle', 'Fill', true, ...
            'Size', 10, 'FillColor','Custom','CustomFillColor',greenColor, 'Opacity', 1.0);
        
        blankImg = uint8(zeros(size(frame)));
        
        % Drawing the line segments
        linesToDraw = [];
        % Drawing the left boundary
        % Checking if it intercepts left frame or bottom frame
        m = tand(leftBoundary); % Slope of the line
        
        % Replacing 90 deg slope with 89 / -90 with -89
        if(abs(m) > 100)
            m = sign(m) * 100;
        end
        
        leftIntercept = m + vanishPoint(2) - m * vanishPoint(1);
        if(leftIntercept < size(frame, 1))
            debugImg = drawLineSegment(debugImg, vanishPoint, [1, leftIntercept]);
            blankImg = drawLineSegment(blankImg, vanishPoint, [1, leftIntercept]);
            %linesToDraw = [linesToDraw; uint32([vanishPoint, 1, leftIntercept])];
        else
            % Checking for the bottom intercept 
            bottomIntercept = (size(frame, 1) - vanishPoint(2) + m*vanishPoint(1))...
                            / m;
            debugImg = drawLineSegment(debugImg, vanishPoint, ...
                                        [bottomIntercept, size(frame, 1)]);
            blankImg = drawLineSegment(blankImg, vanishPoint, ...
                                        [bottomIntercept, size(frame, 1)]);
            %linesToDraw = [linesToDraw; uint32([vanishPoint, ...
            %                                bottomIntercept, size(frame, 1)])];
        end
        
        % Drawing the line segments
        %lanePen = vision.ShapeInserter('Shape','Lines','BorderColor',...
        %'Custom','CustomBorderColor', uint8([0 0 220]), 'Antialiasing', false, ...
        %'LineWidth', 10, 'Opacity', 1.0);
        
        % Drawing the right boundary
        % Checking if it intercepts left frame or bottom frame
        m = tand(rightBoundary); % Slope of the line
        
        % Replacing 90 deg slope with 89 / -90 with -89
        if(abs(m) > 100)
            m = sign(m) * 100;
        end
        
        rightIntercept = m * size(frame, 2) + vanishPoint(2) - m * vanishPoint(1);
        if(rightIntercept < size(frame, 1))
            debugImg = drawLineSegment(debugImg, vanishPoint, ...
                                        [size(frame, 2), rightIntercept]);
            blankImg = drawLineSegment(blankImg, vanishPoint, ...
                                        [size(frame, 2), rightIntercept]);
            % Also drawing on a plane black image
            linesToDraw = [linesToDraw; uint32([vanishPoint, ...
                                            size(frame, 2), rightIntercept]), ];
        else
            % Checking for the bottom intercept 
            bottomIntercept = (size(frame, 1) - vanishPoint(2) + m*vanishPoint(1))...
                            / m;
            debugImg = drawLineSegment(debugImg, vanishPoint, ...
                                        [bottomIntercept, size(frame, 1)]);
            blankImg = drawLineSegment(blankImg, vanishPoint, ...
                                        [bottomIntercept, size(frame, 1)]);
            %linesToDraw = [linesToDraw; uint32([...
            %                                bottomIntercept, size(frame, 1)]), vanishPoint];
        end
        
        % Drawing the vanishing point
        %debugImg = step(vpMarker, debugImg, uint32(vanishPoint));
        
        % Drawing a transparent color filling of white in between the two
        % extremes
        %lanePen = vision.ShapeInserter('Shape','Lines','BorderColor',...
        %'Custom','CustomBorderColor', uint8([0 0 220]), ...
        %'Antialiasing', true, 'LineWidth', 1);
        
        %blankImg = uint8(zeros(size(frame)));
        %blankImg = step(lanePen, blankImg, linesToDraw);
        % Detecting the boundaries and applying a white transparent shade
        redChannel = blankImg(:, :, 1) > 0;
        [~, startCol]= max(redChannel, [], 2);

        % Flipping and finding the other end of the max
        flipped = flip(redChannel, 2);
        [~, endCol] = max(flipped, [], 2);
        
        % Adjusting the end column
        endCol = size(frame, 2) + 1 - endCol;

        mask = zeros(size(frame, 1), size(frame, 2));
        leftAll = false;
        rightAll = false;
        
        for i = uint32(vanishPoint(2)):size(mask, 1)
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
            %if(i > vanishPoint(2) && ...
            %     abs(endCol(i) - startCol(i)) < abs(endCol(i-1) - startCol(i-1)) && ...
            %     fillAll == false)
            %    fillAll = true;
            %end

            %if(fillAll)
            %    startCol(i) = 1;
            %    endCol(i) = size(mask, 2);
            %end
            
            %fprintf('%d %d %d\n', i, startCol(i), endCol(i));
            mask(i, startCol(i) : endCol(i)) = 1;
        end
        
        %error('Returned')
        % Reading the picture for hte paper and drawing the expanse on it
        %canFrame = imread('paper-figures/basic-frame20.png');
        
        %zeroImg = zeros(size(mask));
        %addMask = cat(3, mask, zeroImg, zeroImg);
        %debugImg = canFrame + uint8(addMask) * 100;
        %debugImg = step(lanePen, debugImg, linesToDraw);
        
        %blankImg = uint8(zeros(size(frame)));
        %blankImg = step(lanePen, blankImg, linesToDraw);
        
        %linesToDraw = uint32(linesToDraw);
        %if(size(linesToDraw, 1) > 0)
        %    debugFrame = step(lanePen, debugFrame, linesToDraw(1,:));
        %end
        % Dilate to get thick lines
        %se = strel('ball',5,);
        %blankImg = imdilate(blankImg(:, :, 3)>0, ones(7));
        %darkImg = uint8(zeros(size(blankImg)));
        %darkMask = cat(3, darkImg, darkImg, 255*blankImg);
        
        %debugImg = debugImg + darkMask;
        %debugImg = step(vpMarker, debugImg, uint32(vanishPoint)');
        %imwrite(debugImg, 'paper-figures/vanish-point.png');
        %figure(1) ;imshow(debugImg)
        %darkImg = zeros(size(blankImg));
        %mask = cat(3, blankImg, darkImg, darkImg);
        %debugImage = frame + 255 * uint8(mask);
        
        %figure(1); imshow(debugImg)
        %imwrite(debugImg, 'paper-figures/vanish-point.png');
        %error('Halt the program');
        %figure(1); imshow(mask)
        %figure(2); imshow(blueChannel)
        %figure(1); imshow(debugImg)
        %imwrite(debugImg, 'paper-figures/vanish-point.jpg');
        %figure(2); imshow(blankImg)
       
        %figure(1); imshow(mask)
    end
end