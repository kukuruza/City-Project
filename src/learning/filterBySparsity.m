function statuses = filterBySparsity (mask, cars, statuses, varargin)
    parser = inputParser;
    addRequired(parser, 'mask', @(x) islogical(x) && ismatrix(x));
    addRequired(parser, 'cars', @(x) isempty(x) || isa(x, 'Car'));
    addRequired(parser, 'statuses', @(x) isvector(x));
    addParameter(parser, 'DensitySigma', 0.7, @isscalar);
    addParameter(parser, 'DensityRatio', 2.0, @isscalar);
    addParameter(parser, 'verbose', 0, @isscalar);
    parse (parser, mask, cars, statuses, varargin{:});
    parsed = parser.Results;
    verbose = parsed.verbose;

    whites = ones(size(mask,1),size(mask,2));
    for i = 1 : length(cars)
        center = cars(i).getCenter();
        sigma = double(cars(i).bbox(3) + cars(i).bbox(4)) / 2 * parsed.DensitySigma;
        sz = floor(sigma * 2.5);
        %sigma
        gaussKernel = fspecial('gaussian', sz * 2 + 1, sigma);

        roi = cars(i).getROI();
        maskInside = zeros (size(mask,1), size(mask,2));
        maskInside(roi(1):roi(3), roi(2):roi(4)) = mask(roi(1):roi(3), roi(2):roi(4));
        insideResponse = filterOnce (maskInside, center, sz, gaussKernel, 'verbose', verbose);
        whitesInside = zeros (size(whites,1), size(whites,2));
        whitesInside(roi(1):roi(3), roi(2):roi(4)) = 1;
        insideNorm = filterOnce (whitesInside, center, sz, gaussKernel);
        assert (insideNorm ~= 0);
        insideDensity = insideResponse / insideNorm;
        %fprintf ('insideDensity %f, insideNorm %f\n', insideDensity, insideNorm);

        roi = cars(i).getROI();
        maskOutside = mask;
        maskOutside(roi(1):roi(3), roi(2):roi(4)) = 0;
        outsideResponse = filterOnce (maskOutside, center, sz, gaussKernel, 'verbose', verbose);
        whitesOutside = whites;
        whitesOutside(roi(1):roi(3), roi(2):roi(4)) = 0;
        outsideNorm = filterOnce (whitesOutside, center, sz, gaussKernel, 'verbose', verbose) ...
                    + 0.001;  % this is to avoid /0
        assert (outsideNorm ~= 0);
        outsideDensity = outsideResponse / outsideNorm;
        %fprintf ('outsideDensity %f, outsideNorm %f\n', outsideDensity, outsideNorm);

        density = insideDensity / outsideDensity;
        if density < parsed.DensityRatio
            if parsed.verbose > 1
                fprintf ('    car %d - density %f (bad)\n', i, density); 
            end
            statuses{i} = 'too dense';
        else
            if parsed.verbose > 1
                fprintf ('    car %d - density %f (ok)\n', i, density); 
            end
        end
    end
end

function result = filterOnce (mask, center, sz, kernel, varargin)
%     parser = inputParser;
%     addRequired(parser, 'mask', @ismatrix);
%     addRequired(parser, 'center', @(x) isvector(x) && length(x) == 2);
%     addRequired(parser, 'sz', @isscalar);
%     addRequired(parser, 'kernel', @ismatrix);
%     addParameter(parser, 'verbose', 0, @isscalar);
%     parse (parser, mask, center, sz, kernel, varargin{:});
%     parsed = parser.Results;

    assert (ismatrix(mask));
    mask = double(mask);
    kernel = kernel (max(1, sz-center(1)+2) : min(sz*2+1, sz+1+size(mask,1)-center(1)), ...
                     max(1, sz-center(2)+2) : min(sz*2+1, sz+1+size(mask,2)-center(2)));
    mask = mask (max(1, center(1)-sz) : min(center(1)+sz, size(mask,1)), ...
                 max(1, center(2)-sz) : min(center(2)+sz, size(mask,2)));
    result = mask .* kernel;
%     if parsed.verbose > 2
%         figure(2)
%         imagesc(result);
%         colormap('gray')
%         pause;
%     end
    result = sum(result(:));
end

