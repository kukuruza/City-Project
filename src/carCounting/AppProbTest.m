 function [ProbCol, ProbHOG] = AppProbTest (car1, car2)

% tmp_foldername = 'testdata\';
% filenames=dir(fullfile(tmp_foldername,'*-*-*.*'));
% file={filenames.name};
% n_samples=numel(file);
% 
% car1=imread(fullfile(tmp_foldername,file{1}));
% car2=imread(fullfile(tmp_foldername,file{5}));


% HOG
run('C:\Users\Lotus\Documents\MATLAB\vlfeat-0.9.19-bin\vlfeat-0.9.19\toolbox\vl_setup.m');
carRe1 = imresize(car1,[64 48]);
carRe2 = imresize(car2,[64 48]);
HOG1 = vl_hog(single(carRe1), 4);
HOG2 = vl_hog(single(carRe2), 4);
m1 = numel(HOG1);
m2 = numel(HOG2);
feat1 = reshape(HOG1, 1, m1);
feat2 = reshape(HOG2, 1, m2);
hist1 = zeros(m1);
hist2 = zeros(m2);
hist1 = feat1/ sum(feat1(:)); % normalize, better for all probabilistic methods
hist2 = feat2/ sum(feat2(:));

dHOG = chi_square_statistics(hist1,hist2);
ProbHOG = 1-dHOG;

% Color
n_bins=4;
edges=(0:(n_bins-1))/n_bins;
histogram1=zeros(n_bins,n_bins,n_bins);
histogram2=zeros(n_bins,n_bins,n_bins);
histograms1=zeros(n_bins,n_bins,n_bins);
histograms2=zeros(n_bins,n_bins,n_bins);


IR=imresize(car1,[64 48]);
IR=im2double(IR);
[~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
[~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
[~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;

for j=1:numel(r_bins)
    histogram1(r_bins(j),g_bins(j),b_bins(j)) = histogram1(r_bins(j),g_bins(j),b_bins(j)) + 1;
end
histograms1= reshape(histogram1,1,[]) / sum(histogram1(:)); % normalize, better for all probabilistic methods

IR=imresize(car2,[64 48]);
IR=im2double(IR);
[~,r_bins] = histc(reshape(IR(:,:,1),1,[]),edges); r_bins = r_bins + 1;
[~,g_bins] = histc(reshape(IR(:,:,1),1,[]),edges); g_bins = g_bins + 1;
[~,b_bins] = histc(reshape(IR(:,:,1),1,[]),edges); b_bins = b_bins + 1;

for j=1:numel(r_bins)
    histogram2(r_bins(j),g_bins(j),b_bins(j)) = histogram2(r_bins(j),g_bins(j),b_bins(j)) + 1;
end
histograms2= reshape(histogram2,1,[]) / sum(histogram2(:)); % normalize, better for all probabilistic methods

dCol = chi_square_statistics(histograms1,histograms2);
ProbCol = 1-4 * dCol;
end