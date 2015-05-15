im = imread('~/Desktop/im2.png');

im = imresize(im, [64 64]);

im = rgb2gray(im);
figure(1);
imshow(im);

%im = rgb2gray(im);
%im = histeq(im, normpdf((0:0.05:1), 0.5, 0.2));

%im = imadjust(im);
%im = adapthisteq(im);
%im = medfilt2(im, [5 5]);
%im = wiener2(im,[5 5]);

levelAff = 0.15;
levelShift = 0.05;
H = eye(3,3);
H(1:2, 1:2) = H(1:2, 1:2) + (rand(2,2) - 0.5) * levelAff;
H(1:2, 3) = H(1:2, 3) + (rand(2,1) - 0.5) * levelShift * size(im,1);
im = warpH(im, H);

im = im(4:61, 4:61);
im = imresize(im, [54 54]);


figure(2);
imshow(im);


