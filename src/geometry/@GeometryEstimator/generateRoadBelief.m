function[debugFrame, lanes] = generateRoadBelief(obj, foreground, frame)
    % Function to generate the belief of the road using the foreground and
    % inverse perspective map of the road
    
    laneRatio = 0.5;
    laneWidth = obj.imageSize(2) * 0.25;
    % Computing the inverse perspective transform, for the first time
    if(isempty(obj.warpSize))
        obj.ipHomography = obj.computeIPTransform(foreground, laneRatio, laneWidth); 

        % Find the tight fit warp size ( first time, use a large row size)
        warpedFrame = warpH(frame, obj.ipHomography, ...
                            [3*laneRatio, 1.0, 1.0] .* size(frame));
                        
        background = sum(warpedFrame, 3) == 0;
        [~, maxRowSize] = max(sum(background, 2));
        obj.warpSize = [maxRowSize, size(frame, 2), size(frame, 3)];
    end
    
    % Valid range for histogram
    minCol = obj.imageSize(2)/2 - laneWidth;
    maxCol = obj.imageSize(2)/2 + laneWidth;
    
    % Warping the foreground
    warpedBackground = warpH(foreground, obj.ipHomography, obj.warpSize);
    warpedBackground = warpedBackground(:, minCol:maxCol);
    
    % Check if roadBelief has been initiated
    if(size(obj.roadBelief, 1) > 0)
        obj.roadBelief = obj.roadBelief + sum(warpedBackground); 
    else
        obj.roadBelief = sum(warpedBackground); 
    end
    
    % Smoothen the belief and estimate the number of minima
    windowSize = 7;
    normBelief = obj.roadBelief ./ sum(obj.roadBelief);
    smoothBelief = smooth(normBelief, windowSize)'; % Make it a row vector
    
    % plotting the smoothbelief (debug)
    figure(2); plot(smoothBelief)
    
    % Finding the points of minima based on being a local minima
    minimaRange = 5;
    localMinima = colfilt(smoothBelief, [1, minimaRange], 'sliding', @min);
    
    % Removing the zero pad in the beginning and the end
    compareRange = (minimaRange+1):(length(localMinima)-minimaRange);
    localMinima = localMinima(compareRange) == smoothBelief(compareRange);
    
    % Finding transitions and locations of lane edges
    transitions = [0, ...
       ((localMinima(2:end-1) ~= localMinima(1:end-2))|(localMinima(2:end-1) ~= localMinima(3:end))) ...
       & localMinima(2:end-1), ...
                   0];
               
    % Adding all the offsets
    laneEdges = find(transitions == 1) + minimaRange + minCol;
    
    % Re-projecting it back to the image, for drawing the lanes
    imgPts = obj.ipHomography \ [laneEdges; ...
                            %size(warpedBackground, 1) * ones(1, length(laneEdges));...
                            0.90 * obj.imageSize(1) * ones(1, length(laneEdges));...
                            ones(1, length(laneEdges))];
    
    % Converting from homogeneous to non-homogeneous
    imgPts = [imgPts(1, :) ./ imgPts(3, :); imgPts(2, :) ./ imgPts(3, :)]; 
    
    lanes = zeros(size(imgPts));
    % Creating the equations for the lanes
    for i = 1:length(imgPts)    
        lanes(1, i) = (imgPts(2, i) - obj.road.vanishPt(2)) /...
                        (imgPts(1, i) - obj.road.vanishPt(1));
        lanes(2, i) = obj.road.vanishPt(2) - lanes(1, i) * obj.road.vanishPt(1);
    end
    
    debugFrame = frame;
    
    % Drawing the points on the image
    %lanePen = vision.ShapeInserter('Shape','Lines','BorderColor',...
    %    'Custom','CustomBorderColor', uint8([0 0 220]));% ...
        %'Antialiasing', false, 'LineWidth', 5);
        
    %linesToDraw = [];
    blankImg = zeros(size(frame));
    for i = 1:size(imgPts, 2)
        %linesToDraw = [linesToDraw; [obj.road.vanishPt', imgPts(:, i)']];
        %blankImg = drawLineSegment(blankImg, obj.road.vanishPt, imgPts(:, i));
        debugFrame = drawLineSegment(debugFrame, obj.road.vanishPt, imgPts(:, i));
        %debugFrame = step(lanePen, debugFrame, uint32([100 100 200 200; 100 100 200 100]));
        %debugFrame = step(lanePen, debugFrame, uint32([obj.road.vanishPt', imgPts(:, i)']));
    end
    %linesToDraw = uint32(linesToDraw);
    %if(size(linesToDraw, 1) > 0)
    %    debugFrame = step(lanePen, debugFrame, linesToDraw(1,:));
    %end
    % Dilate to get thick lines
    %se = strel('ball',5,);
    %blankImg = imdilate(blankImg(:, :, 1)>0, ones(3));
    %darkImg = zeros(size(blankImg));
    %mask = cat(3, blankImg, darkImg, darkImg);
    %debugImage = frame + 255 * uint8(mask);
    %figure(1); imshow(debugImage)
    %imwrite(debugImage, 'paper-figures/marked-lanes.png');
    %imwrite(debugFrame, 'paper-figures/marked-lanes.png');
    % Computing and incorporating hough lines
    %warpedFrame = warpH(frame, ipHomography, ...
    %                        [laneRatio, 1.0, 1.0] .* size(frame));
    %warpedFrame = warpH(frame, obj.ipHomography, ...
    %                        [2.5*laneRatio, 1.0, 1.0] .* size(frame));
    
    %figure(4); imshow(warpedFrame)
    %wFrame = warpedFrame(:, 105:625, :);
    % Resizing individual channels
    %resizedWarp = uint8(zeros(size(frame)));
    %warpSize = [size(frame, 1), size(frame, 2)];
    %for i = 1:3
    %    resizedWarp(:, :, i) = imresize(wFrame(:, :, i), warpSize);
    %end
    
    %resizedWarp = imresize(warpedFrame, size(frame));
    %figure(5); imshow(resizedWarp)
    %pause()
    %imwrite(resizedWarp, 'paper-figures/warped-frame.png');
    % 106 623
    %verticalLines = computeHoughLanes(warpedFrame);
    
    %imgPts = zeros(1, numel(verticalLines));
    %for i = 1:numel(verticalLines)
    %    imgPts(i) = mean([verticalLines(i).point1(1), verticalLines(i).point2(1)]);
    %end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Drawing the lines with green
    % Re-projecting it back to the image, for drawing the lanes
    %imgPts = ipHomography \ [imgPts; ...
    %                        %size(warpedBackground, 1) * ones(1, length(laneEdges));...
    %                        0.90 * obj.imageSize(1) * ones(size(imgPts));...
    %                        ones(size(imgPts))];
    
    % Converting from homogeneous to non-homogeneous
    %imgPts = [imgPts(1, :) ./ imgPts(3, :); imgPts(2, :) ./ imgPts(3, :)]; 
    
    % Drawing the points on the image
    %for i = 1:size(imgPts, 2)
        %debugFrame = drawLineSegment(debugFrame, obj.road.vanishPt, imgPts(:, i),...
        %                        uint8([0, 255, 0]));
    %end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Debug block
    debug = true;
    if(debug)
        figure(1); imshow(debugFrame)
    end
end
