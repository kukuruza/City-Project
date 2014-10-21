% test car detector
% 

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run ../subdirPathsSetup.m


%% input and ground truth

imDir = [CITY_DATA_PATH 'testdata/detector/'];

imPath{1} = [imDir 'cam672-0000.jpg'];
imPath{2} = [imDir 'cam672-0002.jpg'];
imPath{3} = [imDir 'cam672-0003.jpg'];
imPath{4} = [imDir 'cam672-0005.jpg'];

% bounding boxes in input images are taken from CarCount test
% x1 y1 width height
bboxes{1} = ...
[151 248 88 66; ...   % #1
 235 180 36 27; ...   % #2
 169 169 44 33; ...   % #3
 118 181 40 30; ...   % #4
 255 160 28 21  ...   % #5
];

bboxes{2} = ...
[203 210 60 45; ...   % #2
 52 212 92 69; ...    % #3
 1 222 72 54; ...     % #4
 247 167 36 27; ...   % #5
 255 144 36 27; ...   % #6
 91 176 52 39; ...    % #7
 151 163 36 27 ...    % #8
];

bboxes{3} = ...
[42 323 168 126; ...  % #2
 227 187 48 36; ...   % #5
 255 151 28 27; ...   % #6
 84 187 52 39; ...    % #8
 188 169 36 27; ...   % #9
 169 154 28 21 ...    % #10
];

% expand bounding boxes
percExpand = 0.5; % twice
for iframe = 1 : 3
    im = imread(imPath{iframe});
    bboxes{iframe} = int32(expandBboxes(bboxes{iframe}, percExpand, im));
end


%% check that input patches are correct

% for iIm = 1 : 3
%     im = imread(imPath{iIm});
%     imshow(im);
%     waitforbuttonpress
%     for j = 1 : size(bboxes{iIm},1)
%         bbox = bboxes{iIm}(j,:);
%         patch = im (bbox(2) : bbox(2)+bbox(4)-1, bbox(1) : bbox(1)+bbox(3)-1, :);
%         imshow(patch);
%         waitforbuttonpress
%     end
% end


%% test

% create
modelPath = [CITY_DATA_PATH, 'violajones/models/model1.xml'];
detector = CascadeCarDetector (modelPath);

% detect
for iIm = 1 : 3
    im = imread(imPath{iIm});
    for j = 1 : size(bboxes{iIm},1)
        bbox = bboxes{iIm}(j,:);
        patch = im (bbox(2) : bbox(2)+bbox(4)-1, bbox(1) : bbox(1)+bbox(3)-1, :);

        cars = detector.detect(patch);

        for k = 1 : length(cars)
            patch = insertObjectAnnotation(patch, 'rectangle', cars(k).bbox, 'car');
        end
        imshow(patch);
        waitforbuttonpress;
    end
end





