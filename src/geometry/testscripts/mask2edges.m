function [edges, roi_mask] = mask2edges(mask0, varargin)

    parser = inputParser;
    addRequired(parser, 'mask0', @(x) ismatrix(x) && isa(x, 'uint8'));
    addParameter(parser, 'MinSize', 3, @isscalar);
    addParameter(parser, 'DilateEdge', 1, @isscalar);
    addParameter(parser, 'verbose', 0, @isscalar);
    parse (parser, mask0, varargin{:});
    parsed = parser.Results;

    % get edges from the map. Hard edges - white, soft edges - gray
    mask = imdilate (mask0, strel('disk', parsed.DilateEdge));
    roi_mask = mask > parsed.MinSize;
    edges = edge(roi_mask, 'Sobel');
    edges = uint8(edges) * 255;
    edges (edges & mask0 > 0) = 128;
