function [azimuths0, mask0] = lanes2azimuth (im0, varargin)
% compute azimuth map, based on tangents to lines.
% Args:
%   im0:  map of lanes
% Returns:
%   azimuths0:  map of azimuths, in degrees
%               0 azimuth is North (to min Y), 90 deg. is East (to max X)
%   mask0:      binary mask, which equals True where aziuths are defined
%

% parsing input
parser = inputParser;
addRequired(parser,  'im0',                     @ismatrix);
addParameter(parser, 'Rad',               20.0, @isscalar);
addParameter(parser, 'MinPoints4Fitting', 20.0, @isscalar);
addParameter(parser, 'verbose',           0,    @isscalar);
parse (parser, im0, varargin{:});
Rad               = parser.Results.Rad;
MinPoints4Fitting = parser.Results.MinPoints4Fitting;
verbose           = parser.Results.verbose;

% prepare filters for figuring out direction. 
% filter 'up to down' looks like this:
%   0 0
%   1 1
filter = zeros(Rad*4+1, Rad*4+1);
filter (Rad*2+1 : end, :) = 1;
filters = zeros (Rad*2+1, Rad*2+1, 5);
for i = 1 : 5
    filters(:,:,i) = filter(Rad+1 : end-Rad, Rad+1 : end-Rad);
    filter = imrotate (filter, 45, 'nearest', 'crop');
    if verbose > 1, subplot(1,5,i); imshow(filters(:,:,i)*255); end
end

% array of output angles
azimuths0 = zeros(size(im0));
mask0     = false(size(im0));

% If there are several lanes in the image, process each one separately,
%   because if lanes are too close, angle filter2 must have just one. 
segments_map = bwlabel(logical(im0), 8);
for i_segm = 1 : max(segments_map(:))
    fprintf ('i_segm: %d.\n', i_segm);
    
    % get only one connected component (one lane)
    im = im0 .* double(segments_map == i_segm);
    
    % this is just noise
    if nnz(im) < 10, continue; end
    
    % manage borders by adding transparent pixels
    im = padarray (im, [Rad, Rad], 0);

    % array of angles
    azimuths  = zeros(size(im));
    mask      = false(size(im));
    responses = zeros(size(im));

    counter = 1;
    for y = Rad+1 : size(im,1)-Rad

        if verbose > 1, fprintf('.'); end
        if verbose > 1 && mod(y, 80) == 0, fprintf('\n'); end
        
        for x = Rad+1 : size(im,2)-Rad

            % skip all black pixels first
            if im(y,x) == 0, continue; end

            neighborhood = im(y-Rad : y+Rad, x-Rad : x+Rad);
            [ys, xs] = find (neighborhood > 0);
            if length(xs) < MinPoints4Fitting, continue; end

            % --- find the angle ---
            % curve of degree one
            curve = polyfit(xs, ys, 1);
            % finding the tangent at that point
            tangent = curve(1);
            angle = -atand(tangent);

            % --- pick one of the two directions ---
            % pick the filter with the closest angle from the list
            [~, ind] = min(abs(angle - [-90, -45, 0, 45, 90]));
            filter = filters(:,:,ind);
            % first half of the filter is all ones, the second half is zeros
            response1 = conv2 (neighborhood, filter, 'valid');
            norm1     = conv2 (double(neighborhood > 0), filter, 'valid');
            % second half of the filter is all minus ones, the first -- zeros
            filter = filter - 1;
            response2 = conv2 (neighborhood, filter, 'valid');
            norm2     = conv2 (double(neighborhood > 0), filter, 'valid');
            % difference between normalized outputs from two halves
            response = response2 / norm2 - response1 / norm1;
            if response < 0, angle = angle + 180; end
            responses(y,x) = response;

            % now it's counter-clockwise, zero is oriented along X
            % fix to clockwise, zero is origented along Y
            angle = 90 - angle;

            % we want the range [0, 360)
            azimuths(y, x) = mod(angle, 360);
            mask(y, x) = true;
            counter = counter + 1;

        end
    end
    if verbose > 1, fprintf('\n'); end
    
    % crop to the original size
    azimuths = azimuths (Rad+1 : end-Rad, Rad+1 : end-Rad);
    mask     = mask (Rad+1 : end-Rad, Rad+1 : end-Rad);
    
    if verbose > 0, imagesc(azimuths, [0, 360]); waitforbuttonpress; end

    % only overwrite empty pixels
    azimuths0 = azimuths0 + double(~mask0) .* azimuths;
    mask0 = mask0 | mask;
    
end  % i_segm

end