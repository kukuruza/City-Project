function F = roadSoapFilm (F, mask, varargin)
%%SOAPFILM interpolates 'F' map based on its values in 'mask'-ed areas
%
% The function fills F(x,y) values based on equations of soap film.
% For every point equation holds: 
%   F(x,y) = (F(x,y-1) + F(x-1,y) + F(x,y+1) + F(x+1,y)) / 4
%
% Input arguments:
%
%     F should be defined in mask-ed areas
%
%     mask-ed areas are considered to be contours. Contours must be closed.
%         There are too types of contours - hard and soft.
%         Soft are initialized as weighted mean from around.
%

parser = inputParser;
addRequired(parser, 'F', @ismatrix);
addRequired(parser, 'mask', @(x) ismatrix(x) && isa(x, 'uint8'));
addParameter(parser, 'Thresh', 0.01, @(x) isnumeric(x) && (isscalar(x) || isvector(x)));
addParameter(parser, 'SizeContour', 20, @(x) isnumeric(x) && (isscalar(x) || isvector(x)));
addParameter(parser, 'SizeBody', 10, @(x) isnumeric(x) && (isscalar(x) || isvector(x)));
addParameter(parser, 'video', []);
addParameter(parser, 'verbose', 0, @isscalar);
parse (parser, F, mask, varargin{:});
parsed = parser.Results;
assert (all(size(F) == size(mask)));


%% contours

% close countours from bottom and sides
F = padarray (F, [1 1]);
mask = padarray (mask, [1 1], 127);
mask(1,:) = 0;

if parsed.verbose > 1, imshow(mask == 0); waitforbuttonpress; end

% fill contours, including borders
for i = 1:length(parsed.SizeContour)
    fprintf ('contour with size: %d, threshiold %f\n', parsed.SizeContour(i), parsed.Thresh(i));
    F = soapFilm (F, mask == 255, 'ignore', mask == 0, ...
                    'size', parsed.SizeContour(i), 'Thresh', parsed.Thresh(i), ...
                    'video', parsed.video, 'verbose', parsed.verbose);
end

if parsed.verbose > 1, imagesc(F); waitforbuttonpress; end


%% body

for i = 1:length(parsed.SizeBody)
    fprintf ('body with size: %d, threshiold %f\n', parsed.SizeBody(i), parsed.Thresh(i));
    F = soapFilm (F, mask > 0, ...
                  'size', parsed.SizeBody(i), 'Thresh', parsed.Thresh(i), ...
                  'video', parsed.video, 'verbose', parsed.verbose);
end

if parsed.verbose > 1, imagesc(F); waitforbuttonpress; end


%% clean up

% everything that is connected to the (upper) border is zero-ed
maskInside = xor(mask, imclearborder (mask == 0, 4));
if parsed.verbose > 1, imagesc(maskInside); waitforbuttonpress; end
F (~maskInside) = 0;

% remove extra borders
F = F(2:size(F,1)-1, 2:size(F,2)-1);

end


function F = soapFilm (F, hard, varargin)
    parser = inputParser;
    addRequired(parser, 'F', @ismatrix);
    addRequired(parser, 'mask', @(x) islogical(x) && ismatrix(x));
    addParameter(parser, 'ignore', [], @(x) ismatrix(x) && islogical(x));
    addParameter(parser, 'Size', 1, @isscalar);
    addParameter(parser, 'MaxNumIter', 10000, @isscalar);
    addParameter(parser, 'Thresh', 0.1, @isscalar);
    addParameter(parser, 'video', []);
    addParameter(parser, 'verbose', 0, @isscalar);
    parse (parser, F, hard, varargin{:});
    
    parsed = parser.Results;
    sz = parsed.Size;
    F = parsed.F;
    hard = parsed.mask;
    ignore = parsed.ignore;
    if isempty(ignore), ignore = false(size(hard)); end

    if parsed.verbose > 2
        imagesc(hard);
        waitforbuttonpress
        imagesc(ignore);
        waitforbuttonpress
        imagesc(~hard & ~ignore);
        waitforbuttonpress
    end

    se = fspecial('average', sz * 2 + 1);
    
    F = padarray (F, [sz sz]);
    hard = padarray (hard, [sz sz]);
    ignore = padarray (ignore, [sz sz], true);

    F0 = F;
    for it = 1 : parsed.MaxNumIter
        F1 = F;
        
        % average
        F = imfilter (F, se, 'replicate');
        ignore_filt = imfilter (double(~ignore), se, 'replicate');
        
        % adjust for ignore
        F = F ./ ignore_filt;
        F(isnan(F)) = 0;
        F(ignore) = 0;
        
        % reset hard constraints
        F(hard) = F0(hard);

        if parsed.verbose > 0
            imagesc(F);
            pause (0.1)
        end
        if ~isempty(parsed.video)
            writeVideo (parsed.video, getframe);
        end
        
        % exit condition on threshold
        dF = F - F1;
        delta = sum(abs(dF(~ignore))) / double(numel(dF(~ignore)));
        if parsed.verbose > 0
            fprintf ('iter: %d, delta: %f\n', it, delta);
        end
        if delta < parsed.Thresh, break, end
    end
    
    F = F (sz+1 : size(F,1)-sz, sz+1 : size(F,2)-sz);
end
