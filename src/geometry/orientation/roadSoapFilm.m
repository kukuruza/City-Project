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
addParameter(parser, 'Thresh', 0.01, @isscalar);
addParameter(parser, 'SizeContour', 20, @isscalar);
addParameter(parser, 'SizeBody', 10, @isscalar);
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
fprintf ('contour with size: %d, threshiold %f\n', parsed.SizeContour, parsed.Thresh);
F = soapFilm (F, mask == 255, 'ignore', mask == 0, ...
                'size', parsed.SizeContour, 'Thresh', parsed.Thresh, ...
                'video', parsed.video, 'verbose', parsed.verbose);

if parsed.verbose > 1, imagesc(F); waitforbuttonpress; end


%% body

fprintf ('body with size: %d, threshiold %f\n', parsed.SizeBody, parsed.Thresh);
F = soapFilm (F, mask > 0, ...
              'size', parsed.SizeBody, 'Thresh', parsed.Thresh, ...
              'video', parsed.video, 'verbose', parsed.verbose);

if parsed.verbose > 1, imagesc(F); waitforbuttonpress; end


%% clean up

% everything that is connected to the (upper) border is zero-ed
maskInside = xor(mask, imclearborder (mask == 0, 4));
if parsed.verbose > 1, imagesc(maskInside); waitforbuttonpress; end
F (~maskInside) = 0;

% remove extra borders
F = F(2 : size(F,1)-1, 2 : size(F,2)-1);

end