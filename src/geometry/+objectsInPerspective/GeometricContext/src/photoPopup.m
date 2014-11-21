%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Satwik edit:
%Including an input images arguement
%Original source : function photoPopup(fnData, fnImage, extSuperpixelImage, outdir)
function[cimages, cnames] = photoPopup(inputImage, fnData, fnImage, extSuperpixelImage, outdir)
% photoPopup [fnData] [fnImage] [extSuperpixelImage] [outdir]
% fnData: filename for .mat file containing classifier data
% fnImage: filename for original RGB image
% extSuperpixelImage: filename extension for superpixel image 
% outdir: directory to output results
%
% Example usage: 
% Have data file classifiers_08_22_2005 stored in current directory, the
% original image ../images/103_0354.jpg, and the superpixel image
% '../images/103_0354.pnm.  I want results to go in ../results.  
%
% photoPopup ./classifiers_08_22_2005 ../images/103_0354.jpg pnm ../results 
% 
% Copyright(C) Derek Hoiem, Carnegie Mellon University, 2005
% Current Version: 1.0  09/30/2005


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Satwik Edit:
% Commented out checking number of arguments as additional inputImage in
% supplied

% if nargin~=4
%     disp(' ')
%     disp(['Only ' num2str(nargin) ' arguments given; Requires 4'])
%     disp(' ')
%     disp('photoPopup [fnData] [fnImage] [extSuperpixelImage] [outdir]')
%     disp('fnData: filename for .mat file containing classifier data')
%     disp('fnImage: filename for original RGB image')
%     disp('extSuperpixelImage: filename extension for superpixel image')
%     disp('outdir: directory to output results')
%     disp(' ')
%     disp('Example usage:')
%     disp('Have data file classifiers_08_22_2005 stored in current directory, the')
%     disp(' original image ../images/103_0354.jpg, and the superpixel image');
%     disp(' ../images/103_0354.pnm.  I want results to go in ../results. '); 
%     disp(' ');
%     disp('photoPopup ./classifiers_08_22_2005 ../images/103_0354.jpg pnm ../results ')
%     disp(' ')
%     disp('Copyright(C) Derek Hoiem, Carnegie Mellon University, 2005')
%     disp('Current Version: 1.0  09/30/2005')
%     disp(' ')
%     return;
% end

% load classifiers
load(fnData);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Satwik edit:
%Including paths for access to required methods
addpath('boosting');
addpath('geom');
addpath('mcmc');
addpath('textons');
addpath('tools');
addpath('util');
addpath('tools/misc');
addpath('tools/drawing');
addpath('tools/drawing');
addpath('tools/weightedstats');
addpath('vrml');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Satwik edit:
%Commenting the reading of image, as its supplied as input
% read image
%im = im2double(imread(fnImage));
im = im2double(inputImage);

if isempty(extSuperpixelImage)

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %Satwik Edit
    %Adding the file name if the super pixels are to be calculated
    [imdir, fn] = strtok(fnImage, '/');
    if isempty(fn)
        fn = fnImage;
        imdir = '.';
    else
        while ~strcmp(strtok(fn, '/'), fn(2:end))
            [rem, fn] = strtok(fn, '/');
            imdir = [imdir '/' rem];
        end
        fn = fn(2:end);
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    imsegs = im2superpixels(im);
    
else

    % separate directory from filename
    [imdir, fn] = strtok(fnImage, '/');
    if isempty(fn)
        fn = fnImage;
        imdir = '.';
    else
        while ~strcmp(strtok(fn, '/'), fn(2:end))
            [rem, fn] = strtok(fn, '/');
            imdir = [imdir '/' rem];
        end
        fn = fn(2:end);
    end

    % compute superpixel map
    imsegs.image_name = fn;
    imsegs = APPimages2superpixels(imdir, extSuperpixelImage, imsegs);

end
    
% compute geometry labels and confidences            
[labels, conf_map] = APPtestImage(im, imsegs, vert_classifier, ...
    horz_classifier, segment_density);               

% get confidence maps
[bn, ext] = strtok(fn, '.');
[cimages, cnames] = APPclassifierOutput2confidenceImages(imsegs, conf_map);
return

%Satwik edit:
%Commenting the writing of confidence images, as its supplied as input
 
%for i = 1:length(cnames)
%    imwrite(cimages{1}(:, :, i), [outdir '/' bn '.' cnames{i} '.pgm']);
%end

% get labeled image
%limage = APPgetLabeledImage(im, imsegs, labels.vert_labels, labels.vert_conf, ...
%        labels.horz_labels, labels.horz_conf);     
%imwrite(limage, [outdir, '/', bn, '.l.jpg']);
%imwrite(im, [outdir, '/', fn]);

% get popup model
%APPwriteVrmlModel(imdir, imsegs, labels, outdir);    