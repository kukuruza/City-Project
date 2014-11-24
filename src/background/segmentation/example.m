%im = imread('Stenosis2_Cropped.bmp');
%load('053-car011.mat')
%load('095-car016.mat')
im = imread('patch.png');
imshow(im);
im = double(rgb2gray(im))/255;

[M,N,s] = size(im);

% unaries: M*N matrix
unaries = -im+0.4;
unaries = -im+0.4;


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

[segmentation, energy, min0,min1] = mex_min_marginals(unaries,edges);

figure;
subplot(1,2,1);
imshow(im);

subplot(1,2,2);
imshow(segmentation);

% subplot(1,3,1);
% imshow(segmentation);axis off;  title('Binary Segmentation');
% 
% 
% subplot(1,3,2);
% imagesc(min0); axis off; axis equal; title('Min marginal Label 0');
% 
% 
% subplot(1,3,3);colormap jet
% imagesc(min1); axis off; axis equal; title('Min marginal Label 1');
% 

