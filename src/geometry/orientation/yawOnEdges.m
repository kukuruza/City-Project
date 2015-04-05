function angle_map = yawOnEdges (edges_mask, varargin)
%ANGLESONEDGES takes a mask of edges and assigns angle to every edge
%    Edge mask is split into separate edges, and each edge is processed
%    separately. This eliminates problems in dense areas
%
% edges -- binary mask, edges are masked (white)
%

parser = inputParser;
addRequired(parser, 'edges', @(x) ismatrix(x) && islogical(x));
addParameter(parser, 'MinParticleArea', 10, @isscalar);
addParameter(parser, 'DilateEdge', 1, @isscalar);
addParameter(parser, 'NeighborhoodSize', 3, @isscalar);
addParameter(parser, 'verbose', 0, @isscalar);
parse (parser, edges_mask, varargin{:});
parsed = parser.Results;


% remove small particles
edges_mask = bwareaopen(edges_mask, parsed.MinParticleArea);

% split into individual edges
edges_mask = bwlabel(edges_mask, 8);  % WHY it works with 8?? it should be 4 really
if parsed.verbose > 1
    imshow(label2rgb(edges_mask, 'spring', 'c', 'shuffle'));
    waitforbuttonpress
end

% every edge has a distinct label
labels = unique(edges_mask(:));
% the first is always 0 (for background)
labels(1) = [];

angle_map = zeros(size(edges_mask));

% for every separate edge
if isempty(labels)
    error('all particles are too small');
end
for label = labels'
    edge_mask = edges_mask == label;
    edge_mask = imdilate(edge_mask, strel('disk', parsed.DilateEdge));
    
    if parsed.verbose > 1
        imshow(edge_mask);
        waitforbuttonpress
    end

    % For every pixel on the edges, take a neighborhood, approximate it by a
    % second degree polynomial and find the slope at that point
    [yPts, xPts] = find(edge_mask);

    for i = 1:length(xPts)
        % Take the neighborhood
        %fprintf('%f %f \n', xPts(i), yPts(i));
        hNbrSize = parsed.NeighborhoodSize;

        leftExt = max(1, xPts(i)-hNbrSize);
        rightExt = min(size(edge_mask, 2), xPts(i) + hNbrSize);

        topExt = max(1, yPts(i) - hNbrSize);
        bottomExt = min(size(edge_mask, 1), yPts(i) + hNbrSize);

        % Checking out of bounds error
    %     fprintf('%d\n%d\n%d\n%d\n', leftExt, ...
    %                                 rightExt, ...
    %                                 bottomExt, ...
    %                                 topExt);

        nbrPts = edge_mask(topExt:bottomExt, leftExt:rightExt);
        [x, y] = find(nbrPts);

        if(length(x) > 2)
            % Fitting a curve
            % Curve of degree two
            %curve = polyfit(x, y, 2);
            % Curve of degree one
            curve = polyfit(x, y, 1);

            % Finding the tangent at that point
            %tangent(yPts(i), xPts(i)) = atand(2 * xPts(i) * curve(1) + curve(2));
            angle_map(yPts(i), xPts(i)) = atand(curve(1));

%             % alternative approximation -- weighted least square            
%             unconfidance = zeros(length(x),1);
%             [~,~,alpha,~] = wtls_line (x, y, unconfidance, unconfidance, 0);
%            angle_map (yPts(i), xPts(i)) = alpha;
        end
    end
    
end