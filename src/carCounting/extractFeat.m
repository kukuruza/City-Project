
tmp_foldername = 'testdata\';
filenames=dir(fullfile(tmp_foldername,'*-*-*.*'));
file={filenames.name};
n_samples=numel(file);

%% HOG
run('C:\Users\Lotus\Documents\MATLAB\vlfeat-0.9.19-bin\vlfeat-0.9.19\toolbox\vl_setup.m');
histograms = zeros(n_samples, 5952); %5952???     % must initialize, or there will be an error of "Subscripted assignment dimension mismatch."
for i=1:n_samples
  I=imread(fullfile(tmp_foldername,file{i}));
  IR=imresize(I,[64 48]);
  VLHOG = vl_hog(single(IR), 4);
  m = numel(VLHOG);
  histogram = reshape(VLHOG, 1, m);
  histograms(i,:) = histogram/ sum(histogram(:)); % normalize, better for all probabilistic methods
end

dist_func=@chi_square_statistics;
D=pdist2(histograms,histograms,dist_func);

D(D == 0) = NaN;
n_show_samples=8; % number of samples for the illustration
figure('name','Random images (left) with their best (middle) and worst (right) match');
c = 1;
rand_indices=randperm(numel(file));
for i=1:n_show_samples
  % image we want to match
  I=imread(fullfile(tmp_foldername,file{rand_indices(i)}));
  if numel(size(I)) > 3, I=I(:,:,1:3); end
  subplot(n_show_samples,3,c); imshow(I); c = c + 1;
  
  % best match
  [d,j]=min(D(:,rand_indices(i)));
  I=imread(fullfile(tmp_foldername,file{j}));
  if numel(size(I)) > 3, I=I(:,:,1:3); end
  subplot(n_show_samples,3,c); imshow(I); title(sprintf('Dist: %.3f',d*100)); c = c + 1;
  
  % worst match
  [d,j]=max(D(:,rand_indices(i)));
  I=imread(fullfile(tmp_foldername,file{j}));
  if numel(size(I)) > 3, I=I(:,:,1:3); end
  subplot(n_show_samples,3,c); imshow(I); title(sprintf('Dist: %.3f',d*100)); c = c + 1;
end
% run('C:\Users\Lotus\Documents\MATLAB\vlfeat-0.9.19-bin\vlfeat-0.9.19\toolbox\vl_setup.m');
% 
% HOG1 = vl_hog(single(im1), 4);
% HOG2 = vl_hog(single(im2), 4);
% 
% feat1 = reshape(HOG1, 1, numel(HOG1));
% feat2 = reshape(HOG2, 1, numel(HOG2));
% 
% d1 = histogram_intersection(feat1,feat2);
% d2 = chi_square_statistics(feat1,feat2);
% d3 = kullback_leibler_divergence(feat1,feat2);   % inf
% d4 = jeffrey_divergence(feat1,feat2);            %nan
% d5 = kolmogorov_smirnov_distance(feat1,feat2);
% d6 = match_distance(feat1,feat2);


%% color

n_bins=4;
edges=(0:(n_bins-1))/n_bins;
histograms=zeros(n_samples,n_bins*n_bins*n_bins);
for i=1:n_samples
  I=imread(fullfile(tmp_foldername,file{i}));
  IR=imresize(I,[64 48]);
  IR=im2double(IR);
  
  [~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
  [~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
  [~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;
  
  histogram=zeros(n_bins,n_bins,n_bins);
  for j=1:numel(r_bins)
    histogram(r_bins(j),g_bins(j),b_bins(j)) = histogram(r_bins(j),g_bins(j),b_bins(j)) + 1;
  end
  histograms(i,:) = reshape(histogram,1,[]) / sum(histogram(:)); % normalize, better for all probabilistic methods
end

dist_func=@chi_square_statistics;
D=pdist2(histograms,histograms,dist_func);

D(D == 0) = NaN;
n_show_samples=8; % number of samples for the illustration
figure('name','Random images (left) with their best (middle) and worst (right) match');
c = 1;
rand_indices=randperm(numel(file));
for i=1:n_show_samples
  % image we want to match
  I=imread(fullfile(tmp_foldername,file{rand_indices(i)}));
  if numel(size(I)) > 3, I=I(:,:,1:3); end
  subplot(n_show_samples,3,c); imshow(I); c = c + 1;
  
  % best match
  %[d,j]=min(D(rand_indices(i),:)); % if distances are not symmetric, then
  % it might be useful to try the other order, see below, depending on the
  % definition of the metric
  [d,j]=min(D(:,rand_indices(i)));
  I=imread(fullfile(tmp_foldername,file{j}));
  if numel(size(I)) > 3, I=I(:,:,1:3); end
  subplot(n_show_samples,3,c); imshow(I); title(sprintf('Dist: %.3f',d*100)); c = c + 1;
  
  % worst match
  %[d,j]=max(D(rand_indices(i),:)); % if distances are not symmetric, then
  % it might be useful to try the other order, see below, depending on the
  % definition of the metric
  [d,j]=max(D(:,rand_indices(i)));
  I=imread(fullfile(tmp_foldername,file{j}));
  if numel(size(I)) > 3, I=I(:,:,1:3); end
  subplot(n_show_samples,3,c); imshow(I); title(sprintf('Dist: %.3f',d*100)); c = c + 1;
end








