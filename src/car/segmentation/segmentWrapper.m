function segmentation = segmentWrapper(im, unaries_offset, edge_weight)
%segmentWrapper is a wrapper for Maxflow and its matlab interface.

% defaults
if nargin < 2, unaries_offset = 0.4; end
if nargin < 3, edge_weight = 0.2; end

im = double(rgb2gray(im))/255;

[M,N,~] = size(im);

% unaries: M*N matrix
unaries = -im + unaries_offset;
unaries = -im + unaries_offset;

% Edges: matrix 3*n_edges. Each column contains: first two elements are the
% indices of the terminal nodes (indices start in zero). third element is
% the edge weight. For this example the edge weight is constant.
aux = reshape(0:M*N-1,[M N]);

%vertical edges
node1 = reshape(aux(1:M-1,:),[1 (M-1)*N]);
node2 = reshape(aux(2:M,:),[1 (M-1)*N]);
weight = ones(size(node1))*edge_weight;
edges = [ node1;  node2; weight];

%horizontal_edges
node1 = reshape(aux(:,1:N-1),[1 M*(N-1)]) ;
node2 = reshape(aux(:,2:N),[1 M*(N-1)]) ; 
weight = ones(size(node1))*edge_weight;
edges = cat(2,edges,[ node1;  node2; weight]);

[segmentation, ~, ~, ~] = mex_min_marginals(unaries,edges);
segmentation = logical(segmentation);
