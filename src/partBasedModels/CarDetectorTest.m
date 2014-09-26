%
% Evg: detect objects given an image and perspective bboxes
%

clear all

im = imread('/Users/evg/Box Sync/City Project/data/five camera for 2 min/cameraNumber572/image0024.jpg');
modelPath = '/Users/evg/projects/City-Project/src/partBasedModels/voc-dpm-voc-release5.02/VOC2010/car_final.mat';

detector = CarDetector(modelPath);

offset = [190 190];
ROIs = [190 190 280 280];
i = 1;
roi = ROIs (i,:);
patch = im (roi(2) : roi(4), roi(1) : roi(3));

tic;
cars = detector.detect(patch);
toc

for i = 1 : length(cars)
    car = cars{i};
    orig = reshape(car.orig(1:end-2), [4 length(car.orig(1:end-2))/4])';
    orig = [orig(:,1) + offset(1), orig(:,2) + offset(2), ...
            orig(:,3) + offset(1), orig(:,4) + offset(2)];
    cars{i}.orig(1:40) = reshape(orig', [1 numel(orig)]);
end

cd voc-dpm-voc-release5.02
showboxes(im, cars{1}.orig);
cd ..

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

