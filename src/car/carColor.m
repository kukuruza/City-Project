function color = carColor( car )
%extractCarColor extract the color of an object of class Car as RGB
%   This is a dummy. Shanghang is working on the content


% validate input
parser = inputParser;
addRequired(parser, 'car', @(x) isa(x, 'Car') || isscalar(x));
parse (parser, car);



% useful code goes here

imPatch = double(rgb2gray(car.patch))/255;

[M,N,s] = size(imPatch);

% unaries: M*N matrix
unaries = -imPatch+0.4;
unaries = -imPatch+0.4;


% Edges: matrix 3*n_edges. Each column contains: first two elements are the
% indices of the terminal nodes (indices start in zero). third element is
% the edge weight. For this example the edge weight is constant.
aux = reshape(0:M*N-1,[M N]);

edge_weight = 0.1;

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
mex mex_min_marginals.cpp graph.cpp maxflow.cpp
[segmentation, energy, min0,min1] = mex_min_marginals(unaries,edges);  % segmentation is the 0\1 mask of the patch

IR = segmentation .* imPatch;
n_bins=4;
edges=(0:(n_bins-1))/n_bins;
histogramCol=zeros(n_bins,n_bins,n_bins);
C.histCol=zeros(n_bins,n_bins,n_bins);

IR=imresize(C.patch,[64 48]);
IR=im2double(IR);
[~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
[~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
[~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;

for j=1:numel(r_bins)
    histogramCol(r_bins(j),g_bins(j),b_bins(j)) = histogramCol(r_bins(j),g_bins(j),b_bins(j)) + 1;
end
% normalize, better for all probabilistic methods
C.histCol= reshape(histogramCol,1,[]) / sum(histogramCol(:));



% this is a dummy result
color = [1 0 0];

end

