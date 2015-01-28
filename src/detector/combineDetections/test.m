%% merging detection bbx
clear all;
close all;
clc

imgpath = '/Users/lgui/Dropbox/City-Project/data/testdata/detector/detections';
imgname = '002-clear.png';
imgdetection = '002-detections.png';

for i = 1:7
    fname = sprintf('%s-car00%d',imgname(1:3),i);
    filename = fullfile(imgpath,fname);
    load(filename)
    btemp = [car.bbox(1),car.bbox(2),car.bbox(3)+car.bbox(1),car.bbox(4)+car.bbox(2)];
    bbx(i,[1,2,3,4])=btemp;
    bbx(i,5)=1;
end

im = imread(fullfile(imgpath,imgname));
figure(1);
imshow(im);

imd = imread(fullfile(imgpath,imgdetection));
figure(2);
imshow(imd);

figure(3);
showboxes(im,bbx);

top = merging(bbx,.3);
figure(4);
showboxes(im,top);





