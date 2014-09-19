%
% Evg: detect objects given an image and perspective bboxes
%

im = imread('/Users/evg/Box Sync/City Project/data/five camera for 2 min/cameraNumber572/image24.jpg');
load('/Users/evg/projects/City-Project/src/partBasedModels/voc-dpm-voc-release5.02/VOC2010/car_final.mat')

cd('voc-dpm-voc-release5.02');
startup;

[ds, bs] = process(im, model, model.thresh);

b = getboxes(model, im, ds, reduceboxes(model, bs));
subplot(1,3,2);
showboxes(im, b);

cd ..
