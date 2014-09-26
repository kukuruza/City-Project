%
% Evg: detect objects given an image and perspective bboxes
%

clear all

im = imread('/Users/evg/Box Sync/City Project/data/five camera for 2 min/cameraNumber572/image0024.jpg');
modelPath = '/Users/evg/projects/City-Project/src/partBasedModels/voc-dpm-voc-release5.02/VOC2010/car_final.mat';

detector = CarDetector(modelPath);

ROIs = [190 190 280 280];
i = 1;
roi = ROIs (i,:);
patch = im (roi(2) : roi(4), roi(1) : roi(3));

tic;
cars = detector.detect(patch);
toc

showboxes(im, cars{1}.orig);

return

% ROIs = [190 190 280 280];
% 
% for i = 1 : size(ROIs,1)
% 
%     roi = ROIs (i,:);
%     
%     patch = im (roi(2) : roi(4), roi(1) : roi(3));
%     
%     [ds, bs] = process(patch, model);
%     b = getboxes(model, patch, ds, reduceboxes(model, bs));
%     showboxes(patch, b);
%     
% end

