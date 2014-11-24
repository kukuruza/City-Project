function mask_out = denoiseMask (mask_in, fn_level, fp_level)
%DENOISEFOREGROUNDMASK
% denoise foreground mask.
% That is, significantly increase foreground recall and decrease accuracy
%

% create structural elements for erosion and dilation
seErode = strel('disk', fp_level);
seDilate = strel('disk', fn_level);

% erode and dilate
mask_out = imerode(mask_in, seErode);
mask_out = imdilate(mask_out, seDilate);

