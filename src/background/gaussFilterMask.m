function mask_out = gaussFilterMask (mask_in, gauss_sigma, threshold)
%GAUSSFILTERMASK
% Use convolution with gauss filter and then threshold to refine the mask
% That is, significantly increase foreground recall and decrease accuracy
%

% convolve with Gaussian filter
se = fspecial('gaussian', gauss_sigma * 3, gauss_sigma);
blurry = conv2(single(mask_in), se, 'same');

% threshold by some value
mask_out = im2bw (blurry, threshold);
