%function [vpY, vpX] = my(grayImg, colorImg, norient, outputPath, numOfValidFiles)
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
        outliers(:, :, 1) = (1-candidateVotingMap) .* outliers(:, :, 1) + ...
                            candidateVotingMap .* 255;

        imwrite(unint8(outliers), fullfile(outputPath, ...
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
    maxLocation = round(mean( orientationId .* (normResponse == 100), 3)); 

    % Re-setting the maximum location to 0
    % Lower side boundaries
    [row, col] = find(maxLocation <= 2 & maxLocation > 0);
    % Converting them into linear indices for easier
    linearInds = sub2ind([imageH, imageW], row, col);
    linearInds = sub2ind([imageH, imageW, norient], row, col, maxLocation(linearInds));
    normResponse([linearInds; linearInds+1; linearInds+2]) = 0;

    % Upper side boundaries
    [row, col] = find(maxLocation >= 35);
    % Converting them into linear indices
    linearInds = sub2ind([imageH, imageW], row, col);
    linearInds = sub2ind([imageH, imageW, norient], row, col, maxLocation(linearInds));
    normResponse([linearInds; linearInds-1; linearInds-2]) = 0;

    % Other inside cases
    [row, col] = find(maxLocation > 2 & maxLocation <= 34);
    % Converting them into linear indices
    linearInds = sub2ind([imageH, imageW], row, col);
    linearInds = sub2ind([imageH, imageW, norient], row, col, maxLocation(linearInds));
    normResponse([linearInds+2; linearInds+1;linearInds; linearInds-1; linearInds-2]) = 0;
    
    % Sorted response
    sortedResponse = sort(normResponse, 3, 'descend');
    contrast = (100 - mean(sortedResponse(:, :, 5:15), 3)) .^ 2;

    % Updating the confidence map and orientation map
    updatePixels = maxResponse > 1; % Updating the pixels at which max > 1
    confidenceMap(updatePixels) = contrast(updatePixels);
    orientationMap = (maxLocation - 1) * angleInterval;

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    border = zeros(imageH, imageW);
    border(1+halfKerSize:imageH-halfKerSize, 1+halfKerSize:imageW-halfKerSize) = 1;
    %sum(sum(abs(border.*orientationMap - args.orientationMap)))
    %sum(sum(abs(border.*confidenceMap - args.confidenceMap)))
    %sum(sum(sum(abs(args.tempImage - normResponse .* border(:, :, ones(1,norient))))))
    sum(sum(abs(args.tempImage - maxLocation .* border)))
    %sum(sum(abs(args.tempImage - contrast)))
    %figure; imagesc(confidenceMap)
    %figure; imagesc(args.confidenceMap)

%    vpX = 0; vpY = 0;
%end
