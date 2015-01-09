function[cleanBackground] = generateCleanBackground( refBackground, curBackground, ...
                                                        diffType, fgThreshold)
    % Generates clean background using reference background from a
    % particular lightning conditions and a bakground model trained for
    % current conditions
    %
    % Takes in reference background, current background and type of
    % channels to consider for differencing along with threshold
    % 
    % cleanBackground = generateCleanBackground(refBackground,
    %                           curBackground, diffType, threshold)
    %
    % diffType = 0 - LAB space, 1 - RGB space, 2 - grayscale
    %
    
    
    % Parameters for the function
    debug = false;
    
    filterSize = 50; % Gaussian filter size
    filterSigma = 25.0; % Gaussian filter sigma
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    if(nargin < 3)
        diffType = 0; % Default
        fgThreshold = 70; % Threshold for foreground separation
    end
    
    
    switch diffType
        % LAB space
        case 0
            labTransform = makecform('srgb2lab');
            labReference = applycform(refBackground, labTransform);
            labCurrent = applycform(curBackground, labTransform);
            difference = sqrt(sum(abs(int32(labReference) - int32(labCurrent)) .^ 2, 3));    
            
        % RGB space
        case 1
            difference = sqrt(sum(abs(int32(refBackground) - int32(curBackground)) .^ 2, 3));    
            
        %  Grayscale
        case 2     
            grayReference = rgb2gray(refBackground);
            grayCurrent = rgb2gray(curBackground);
            difference = abs(int32(grayCurrent) - int32(grayReference));
    end
    
    % Thresholding the difference and applying gaussian filter
    fgMask = difference > fgThreshold;
    
    backImage = curBackground;
    backImage(fgMask(:, :, [1 1 1])) = 0;
    
    gaussFilter = fspecial('gaussian', filterSize, filterSigma);
    blurBackImage = imfilter(double(backImage), gaussFilter, 'replicate');
    blurMask =  imfilter(double(~fgMask), gaussFilter, 'replicate');
    
    % Normalizing the blurBackImage as few elements were zero
    elemsToNormalize = (blurMask > 0);
    blurMask = blurMask(:, :, [1 1 1]); % 3channel mask
    
    elemsToNormalize = elemsToNormalize(:, :, [1 1 1]); % 3channel mask
    blurBackImage(elemsToNormalize) = ...
            blurBackImage(elemsToNormalize) ./ blurMask(elemsToNormalize);
    
    % Converting to uint8
    blurBackImage = uint8(blurBackImage);
    cleanBackground = refBackground + (curBackground - blurBackImage) ;
    
    figure(1); imshow(cleanBackground);
end

