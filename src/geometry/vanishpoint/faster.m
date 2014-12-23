%function [vpY, vpX] = faster(grayImg, colorImg, norient, outputPath, numOfValidFiles)
    % If files should be dumped for debugging
    fileDump = false;

    % Speeded up version for vanishing point detection, written in
    % parallel to the author's implementation
    [imageH, imageW] = size(grayImg);
    largestDistance = hypot(imageH, imageW);

    % Finding edges
    edgeImg = edge(grayImg, 'canny');

    %%%%%%%%%%%%%%% Saving the edge image %%%%%%%%%%%%%%%%%%
    if(fileDump) 
        imwrite(edgeImg, fullfile(outputPath, ...
                        sprintf('%d_edgeImage0.jpg', numOfValidFiles)), 'jpg');
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Perform median filtering
    smoothGrayImg = medfilt2(grayImg, [5 5]);

    % Removing vertical short (e.g., 30-pixel long) edges
    vertBarHeight = 31; vertBarWidth = 11;
    halfBarLength = floor(vertBarHeight/2);
    outlierBinary = ones(imageH, imageW);
    candidateVotingMap = edgeImg;

    vertBarSum = colfilt(edgeImg, [vertBarHeight, 1], 'sliding', @sum);
    locations = imdilate(vertBarSum >= 20, ones(vertBarHeight, vertBarWidth));

    candidateVotingMap(locations) = 0;
    outlierBinary(locations) = 0;

    %%%%%%%%%%%%%% Saving the outlier image %%%%%%%%%%%%%%     
    if(fileDump)
        outliers = grayImg(:, :, [1 1 1]);
        outliers(:, :, 1) = (1-candidateVotingMap).*double(outliers(:, :, 1)) + ...
                            candidateVotingMap .* 255;

        imwrite(uint8(outliers), fullfile(outputPath, ...
                sprintf('%d_outliersImage.jpg', numOfValidFiles)), 'jpg');
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Construct Kernels
    angleRange = 180;
    angleInterval = angleRange/norient;
    tmpW = min([imageH, imageW]);
    lamda = 2^(round(log2(tmpW)-5));
    kerSize = round(10*lamda/pi);

    if mod(kerSize,2)==0
        kerSize = kerSize + 1;
        halfKerSize = floor(kerSize/2);
    else
        halfKerSize = floor(kerSize/2);
    end

    oddKernel = zeros(kerSize, kerSize, norient);
    evenKernel = zeros(kerSize, kerSize, norient);
    delta = kerSize/9;
    tmpDelta = -1/(delta*delta*8);
    c = 2*pi/lamda; %%%%
    cc = 2.2; %%%%

    % Pre-computing sine and cosine of angles
    cosTheta = cos( (0:angleRange-1) * pi / 180)';
    sinTheta = sin( (0:angleRange-1) * pi / 180)';

    %%%%%%%%%%%%%%%%%%%%%% kernels generation%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    for theta = 90+1:angleInterval:angleRange-angleInterval+1+90
        tmpTheta = (theta - 1)*pi/180;
        for y= -halfKerSize:halfKerSize
            ySinTheta = y*sin(tmpTheta);
            yCosTheta = y*cos(tmpTheta);
            for x=-halfKerSize:halfKerSize
                xCosTheta = x*cos(tmpTheta);
                xSinTheta = x*sin(tmpTheta);
                a = xCosTheta+ySinTheta;
                b = -xSinTheta+yCosTheta;
                oddKernel(y+halfKerSize+1,x+halfKerSize+1,(theta - 1-90)/angleInterval+1) = exp(tmpDelta*(4*a*a+b*b))*(sin(c*a)-exp(-cc*cc/2));
                evenKernel(y+halfKerSize+1,x+halfKerSize+1,(theta - 1-90)/angleInterval+1) = exp(tmpDelta*(4*a*a+b*b))*(cos(c*a)-exp(-cc*cc/2));
            end
        end
    end

    %%%%%%%%%%%%%%%%% normalize kernels %%%%%%%%%%%%%%%%%%%%%
    normalizedOddKernel = zeros(kerSize, kerSize, norient);
    normalizedEvenKernel = zeros(kerSize, kerSize, norient);
    for i=1:norient
        tmpKernel = oddKernel(:,:,i)-mean(mean(oddKernel(:,:,i)));
        tmpKernel = tmpKernel/(norm(tmpKernel));
        normalizedOddKernel(:,:,i) = tmpKernel;
        
        tmpKernel = evenKernel(:,:,i)-mean(mean(evenKernel(:,:,i)));
        tmpKernel = tmpKernel/(norm(tmpKernel));
        normalizedEvenKernel(:,:,i) = tmpKernel;
    end

    % Image convolution with Gabor filterBanks 
    filteredImgsOdd = zeros(imageH,imageW,norient*1);
    filteredImgsEven = zeros(imageH,imageW,norient*1);
    complexResponse = zeros(imageH,imageW,norient*1);
    for i=1:norient
        filteredImgsOdd(:,:,i) = conv2(double(smoothGrayImg), ...
                                        normalizedOddKernel(:,:,i), 'same');
        filteredImgsEven(:,:,i) = conv2(double(smoothGrayImg), ...
                                        normalizedEvenKernel(:,:,i), 'same');
        complexResponse(:,:,i) = hypot(filteredImgsOdd(:,:,i), ...
                                                filteredImgsEven(:,:,i));
        complexResponse(:,:,i) = complexResponse(:,:,i)/(kerSize*kerSize);
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Region of interest for the active part of the image
    roi = zeros(imageH, imageW);
    roi(1+halfKerSize:imageH-halfKerSize, 1+halfKerSize:imageW-halfKerSize) = 1;
    roi = logical(roi);

    % Evaluating the dominant orientation
    confidenceMap = zeros(imageH,imageW); % Confidence of the edge orientation
    orientationMap = zeros(imageH,imageW); % Map of the most dominent response

    % Finding the maximum/minimum responses from all the directions
    maxResponse = max(complexResponse, [], 3);
    minResponse = min(complexResponse, [], 3);

    % Normalizing the response to within [0, 100]
    normResponse = bsxfun(@minus, complexResponse, minResponse);
    normResponse = 100 * normResponse ./ repmat(maxResponse - minResponse, [1 1 norient]);

    % Finding the mean of the maximum location i.e. where 100 is found
    [~, ~, orientationId] = meshgrid(1:imageW, 1:imageH, 1:norient);
    maxLocation = abs(normResponse - 100) < 1e-5;
    noMaxima = sum(maxLocation, 3);
    % Compute the mean only if number of maxima is greater than zero (avoiding zero division)
    maxLocationIds = sum(orientationId .* maxLocation, 3); 
    nonZeroMaxima = noMaxima > 0;
    maxLocationIds(nonZeroMaxima) = maxLocationIds(nonZeroMaxima) ./ noMaxima(nonZeroMaxima);
    % Aliasing it to maxLocation
    maxLocation = round(maxLocationIds);

    % Re-setting the maximum location to 0
    % Lower side boundaries
    [row, col] = find(maxLocation <= 2 & maxLocation > 0);
    % Converting them into linear indices for easier
    linearInds = sub2ind([imageH, imageW], row, col);
    linearInds = sub2ind([imageH, imageW, norient], ...
                    repmat(row, [3 1]), ...
                    repmat(col, [3 1]), ...
                    [maxLocation(linearInds); maxLocation(linearInds)+1; maxLocation(linearInds)+2]);
    normResponse(linearInds) = 0;

    % Upper side boundaries
    [row, col] = find(maxLocation >= 35);
    % Converting them into linear indices
    linearInds = sub2ind([imageH, imageW], row, col);
    linearInds = sub2ind([imageH, imageW, norient], ...
                    repmat(row, [3 1]), ...
                    repmat(col, [3 1]), ...
                    [maxLocation(linearInds); maxLocation(linearInds)-1; maxLocation(linearInds)-2]);
    normResponse(linearInds) = 0;

    % Other inside cases
    [row, col] = find(maxLocation > 2 & maxLocation <= 34);
    % Converting them into linear indices
    linearInds = sub2ind([imageH, imageW], row, col);
    linearInds = sub2ind([imageH, imageW, norient], ...
                    repmat(row, [5 1]), ...
                    repmat(col, [5 1]), ...
                    [maxLocation(linearInds); maxLocation(linearInds)-1; maxLocation(linearInds)-2; ...
                        maxLocation(linearInds)+1; maxLocation(linearInds)+2]);
    normResponse(linearInds) = 0;
    
    % Sorted response
    sortedResponse = sort(normResponse, 3, 'descend');
    contrast = (100 - mean(sortedResponse(:, :, 5:15), 3)) .^ 2;

    % Updating the confidence map and orientation map
    updatePixels = maxResponse > 1; % Updating the pixels at which max > 1
    confidenceMap(updatePixels) = contrast(updatePixels);
    orientationMap = (maxLocation - 1) * angleInterval;

    % Make response when maxLocation = 0, as zero; only for confidenceMap
    confidenceMap(maxLocation == 0) = 0;
    orientationMap(~logical(roi)) = -1 * angleInterval;

    %%%%%%%%%% Re-scaling and saving the confidence image %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    minVal = min(confidenceMap(roi));
    maxVal = max(confidenceMap(roi));
    confidenceMap(roi) = 255 * (confidenceMap(roi) - minVal)/(maxVal - minVal);

    % Saving the confidence image
    if(fileDump) 
        imwrite(confidenceMap, fullfile(outputPath, ...
                        sprintf('%d_confidenceMap.jpg', numOfValidFiles)), 'jpg');
    end

    % Saving the confidence image, overlapping on gray image
    if(fileDump)
        confidenceMapBinary = (confidenceMap > 30);     
        confOverlapImg = grayImg .* uint8(~confidenceMapBinary);
        confOverlapImg = confOverlapImg(:, :, [1 1 1]);
        confOverlapImg(:, :, 1) = double(confOverlapImg(:, :, 1)) + 255*confidenceMapBinary;

        imwrite(uint8(confOverlapImg), fullfile(outputPath, ...
                        sprintf('%d_confidenceOverlap.jpg', numOfValidFiles)), 'jpg');
    end

    % Saving the orientation image, rescaling by 2
    if(fileDump)
        displayOrientImg = displayOrientationImage(orientationMap, grayImg);
        imwrite(uint8(displayOrientImg), fullfile(outputPath, ...
                        sprintf('%d_orientationBarImg.jpg', numOfValidFiles)), 'jpg');
        imwrite(uint8(orientationMap), fullfile(outputPath, ...
                        sprintf('%d_orientationMap.jpg', numOfValidFiles)), 'jpg');
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % For shadows remove horizontal or nearly horizontal edges
    nonHorizontalEdges = ones(imageH, imageW);
    nonHorizontalEdges(orientationMap == 180) = 0;

    % Voting for vanishing point estimation
    edgeImg = ones(imageH, imageW) .* outlierBinary .* nonHorizontalEdges;
    
    % Indices of edge pixels
    [rowInd, colInd] = find(edgeImg == 1);
    noEdgePixels = sum(edgeImg(:));

    % Variables for voting map
    votingMap = zeros(imageH, imageW);
    interval = 1;
    uppPercent = 0.9;
    halfLargestDistance = largestDistance * 0.5;

    % Change to smaller values for better results in case of extremely 
    % low vanishing points
    halfImgH = round(imageH * 0.4);

    % Given a point on the edge, find the regions it can contribute to
    % Pre-computing few matrices for easier access
    % Point of interest is assumed to be at the bottom point
    % ie (halfImgH, imageW)
    [xInd, yInd] = meshgrid(1:(2*imageW-1) , 1:halfImgH-1);
    distanceMatrix = hypot(xInd - imageW, yInd - halfImgH);
    angleMatrix = 180/pi * acos((imageW - xInd) ./ distanceMatrix);

    % For each point on the edge
    for ptId = 1:noEdgePixels
        rowPt = rowInd(ptId);
        colPt = colInd(ptId);
        
        % Get the row / column ranges for matrix and map
        matRowRange = max(halfImgH - rowPt + 1, 1):halfImgH-1;
        matColRange = imageW-colPt+1:2*imageW-colPt;
        mapRowRange = max(1, rowPt - halfImgH +1):rowPt-1;

        % Get the region of voting for this pixel
        angleDiff = abs(angleMatrix(matRowRange, matColRange) - orientationMap(rowPt, colPt));
        votingRegion = angleDiff < angleInterval;

        distanceSubMatrix = distanceMatrix(matRowRange, matColRange);
        pointVoteMap = zeros(size(distanceSubMatrix));

        % Only at this points
        votingPt = (votingRegion == 1);
        pointVoteMap(votingPt) = exp(-distanceSubMatrix(votingPt) .* angleDiff(votingPt) / halfLargestDistance);

        % Compute its contribution and add it to the voting map
        %pointVoteMap = exp(-distanceMatrix(matRowRange, matColRange) .* angleDiff/halfLargestDistance);
        votingMap(mapRowRange, :) = votingMap(mapRowRange, :) + pointVoteMap;
    end

    % voting map considered only within this region
    votingRoi = zeros(imageH, imageW);
    votingRoi(1:round(imageH * 0.9), halfKerSize+1:imageW-halfKerSize) = 1; 
    votingMap = votingMap .* votingRoi;
    %sum(sum(abs(args.votingMap - votingMap .* votingRoi)))

    %difference = abs(args.votingMap - votingMap.*votingRoi);
    %figure; imagesc(difference)

 %   vpX = 0; vpY = 0;
%end
