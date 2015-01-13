function rgb = mask2rgb(mask)
% convert binary mask to color image, with values [0 0 0] and 255 * [1 1 1]

assert (islogical(mask));
assert (ismatrix(mask));

rgb = im2uint8(mask);
rgb = rgb(:,:,[1 1 1]);
