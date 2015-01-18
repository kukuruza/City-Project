function[adjBackground] = generateCleanBackground( refBackground, curBackground, varargin)
% Generates clean background using reference background from a
% particular lightning conditions and a bakground model trained for
% current conditions
%
% Takes in reference background, current background and type of
% channels to consider for differencing along with threshold
% 
% background = generateCleanBackground(refBackground, curBackground, ...
%                                      'diffType', diffType, ...
%                                      'fgThreshold', fgThreshold)
%
% diffType = 0 - LAB space, 1 - RGB space, 2 - grayscale
%

    parser = inputParser;
    addRequired(parser,  'refBackground',      @(x) ndims(x) == 3 && size(x,3) == 3);
    addRequired(parser,  'curBackground',      @(x) ndims(x) == 3 && size(x,3) == 3);
    addParameter(parser, 'diffType',     0,    @(x) x == 0 || x == 1 || x == 2);
    addParameter(parser, 'filterSigma',  50.0, @isscalar);
    addParameter(parser, 'fgThreshold',  40.0, @isscalar);
    addParameter(parser, 'verbose',      0,    @isscalar);
    parse (parser, refBackground, curBackground, varargin{:});
    parsed = parser.Results;
    
    % Parameters for the function
    debug = false;
    
    filterSize = parsed.filterSigma * 1.5;

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    switch parsed.diffType
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
    
    % thresholding the difference
    fgMask = difference > parsed.fgThreshold;

    % if debug, show values that cannot be blurred
    if debug, fgMask = imdilate(difference > 20, strel('disk',10)); end
    
    % blur both the ref. and the cur. background
    gaussFilter = fspecial('gaussian', filterSize, parsed.filterSigma);
    blurBack = filterWithMask (curBackground, ~fgMask, gaussFilter);
    blurRef  = filterWithMask (refBackground, ~fgMask, gaussFilter);

    % adjust reference background to current conditions
    assert (isa(blurBack, 'double') && isa(blurRef, 'double'));
    adjBackground = uint8(double(refBackground) + (blurBack - blurRef));
    
    if parsed.verbose
        imshow([refBackground, adjBackground; ...
                curBackground, 255*uint8(fgMask(:,:,[1 1 1]))]);
        pause(0.1);
    end
end


% filter only masked areas
function filtered = filterWithMask (image, mask, filter)
    debug = false;

    % blur mask
    blurMask = imfilter(double(mask), filter, 'replicate');
    blurMask = blurMask(:, :, [1 1 1]); % 3channel mask
    
    % blur image
    image (~mask(:,:,[1,1,1])) = 0;
    blurImage = imfilter(double(image), filter, 'replicate');
    
    % normalized blurred image
    filtered = blurImage ./ blurMask;
    
    % if there is no valid value within blur radius, use src value
    if ~debug
        badvalues = isnan(filtered);
        filtered (badvalues) = image(badvalues);
    end
end
    

