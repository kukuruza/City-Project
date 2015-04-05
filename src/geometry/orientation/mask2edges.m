function [edges, roi_mask] = mask2edges(mask0, varargin)

    parser = inputParser;
    addRequired(parser, 'mask0', @(x) ismatrix(x) && isa(x, 'uint8'));
    addParameter(parser, 'MinSize', 3, @isscalar);
    %addParameter(parser, 'DilateEdge', 1, @isscalar);
    addParameter(parser, 'Type', 'Sobel', @ischar); % Sobel or Canny
    addParameter(parser, 'verbose', 0, @isscalar);
    parse (parser, mask0, varargin{:});
    parsed = parser.Results;

    % get edges from the map. Hard edges - white, soft edges - gray
    
    if strcmp(parsed.Type, 'Canny')
        fprintf ('using Canny to find edges\n')
        mask = imdilate (mask0, strel('disk', 2));
        roi_mask = mask > parsed.MinSize;
        edges = edge(roi_mask, 'Canny');
        roi_mask = imerode(roi_mask, strel('disk', 2));
        edges = fixBorder(edges, 1);
    elseif strcmp(parsed.Type, 'Sobel')
        fprintf ('using Canny to find edges\n')
        mask = imdilate (mask0, strel('disk', 1));
        roi_mask = mask > parsed.MinSize;
        edges = edge(roi_mask, 'Sobel');
    else
        error('need either Canny or Sobel');
    end
    
    edges = uint8(edges) * 255;
    edges (edges & mask0 > 0) = 128;

end
function mask = fixBorder(mask, pad)
    mask = mask(1+pad : size(mask,1)-pad, 1+pad : size(mask,2)-pad);
    mask = padarray(mask, [pad pad], 'replicate');
end