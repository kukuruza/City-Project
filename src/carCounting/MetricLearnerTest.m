% 
%

clear all

run ../rootPathsSetup
run ../subdirPathsSetup.m

%% input and ground truth

% input images
imDir = [CITY_DATA_PATH '2-min/camera572/'];
imPath{1} = [imDir 'image0000.jpg'];
imPath{2} = [imDir 'image0002.jpg'];
imPath{3} = [imDir 'image0003.jpg'];

% bounding boxes in input images
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

% intervals between frames in random units
framediff(1) = 1.1;
framediff(2) = 1.6;

% correspondance between cars (row - new.frame, col - prev.frame)
corresp{1} = [];

corresp{2} = ...
[
 0 1 0 0 0; ...
 0 0 1 0 0; ...
 0 0 0 1 0; ...
 0 0 0 0 1; ...
 0 0 0 0 0; ...
 0 0 0 0 0; ...
 0 0 0 0 0 ...
];
% 
% corresp{3} = ...
% [
%  1 0 0 0 0 0 0 0; ...
%  0 0 0 1 0 0 0 0; ...
%  0 0 0 0 1 0 0 0; ...
%  0 0 0 0 0 1 0 0; ...
%  0 0 0 0 0 0 0 0; ...
%  0 0 0 0 0 0 0 0 ...
% ];

corresp{3} = ...
[
 1 0 0 0 0 0 0 ; ...
 0 0 0 1 0 0 0 ; ...
 0 0 0 0 1 0 0 ; ...
 0 0 0 0 0 0 1 ; ...
 0 0 0 0 0 0 0 ; ...
 0 0 0 0 0 0 0  ...
];


%% check that input patches are correct
% 
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


%% do computation

%matFile = 'Geometry_Camera_360.mat';
%geom = GeometryEstimator(frame, matFile);
% Loading the road properties that were manually marked (Pts for the lanes)
% Geometry object can be simply loaded using the object file
% The object geom will be directly loaded. However, newer functionalities
% might need this object to be created again
objectFile = 'GeometryObject_Camera_572.mat';
load(objectFile);
fprintf(strcat('Read Geometry object from file, might not be the latest version\n' , ...
    'Update if made changes to GeometryEstimator class\n'));
counting = MetricLearner(geom); % pass necessary arguments to constructor
count0 = size(bboxes{1},1); % initial should be the number of cars in the first frame

for iframe = 1 : length(bboxes)

    % read frame
    frame = imread(imPath{iframe});
    j = iframe;
     cars = Car.empty;
     for i = 1:length(bboxes{j})
         cars(i) = Car(bboxes{j}(i, :));
         cars(i).getROI ();
         cars(i).extractPatch(frame);
         cars(i).generateFeature(frame);
     end
     
     %In order to read the patch for the ith car
     % cars{i}.features
     % in order to read the bbox
     % cars{i}.bbox
     
     
%     % make cars from bboxes
%     cars = {};
%     for i = 1 : size(bboxes{iframe},1)
%         bboxesF = bboxes{iframe};
%         bboxesCar = bboxesF(i,:);
%         cars{i} = frame(bboxesCar(2) : bboxesCar(2)+bboxesCar(4)-1, bboxesCar(1) : bboxesCar(1)+bboxesCar(3)-1, :);
%         % cars = [cars CarAppearance(bboxesF(i,:))];      
%     end
    


    % counting the new cars and total number of cars for a new frame
    counting.WeightGeom = 0.4;
    counting.WeightHog = 0.4;
    counting.WeightCol = 0.2;
    counting.Th = 0.5;
    TP = 0;
    TN = 0;
    FP = 0;
    FN = 0;
    Acc = 0;
    
    % counting.Th = 0.1:0.05:1;
    for k = 1:19
    counting.Th = 0.1;
    [newCarNumber Match] = counting.processFrame(frame, cars);  % cars is the cell array of the class carappearance, every cell is the carappearance based on every bbox
    
    if(counting.framecounter > 1)
    [m n] =size(Match);
    
%     for p = 1:m
%         for q = 1:n
%             if (Match(p,q)==1 && corresp{iframe}(p,q)==1)
%                 TP = TP +1;
%             elseif (Match(p,q)==0 && corresp{iframe}(p,q)==0)
%                 TN = TN +1;
%             elseif (Match(p,q)==1 && corresp{iframe}(p,q)==0)
%                 FP = FP +1;
%             elseif (Match(p,q)==0 && corresp{iframe}(p,q)==1)
%                 FN = FN +1;
%             end
%         end
%     end
%     
%     Acc(k) = (TP + TN)/(FP +FN);   
    
    count1 = count0 + newCarNumber;    % count1 is the total number of cars for all the frames.
    count0 = count1; 
%     counting.framecounter = counting.framecounter + 1;
%     counting.Th = counting.Th + 0.05;
    end
    
    end
%     counting.Th = 0.1:0.05:1;
%     plot(Acc, counting.Th)
    % compare output with ground truth
    % corresp{iframe}
    
end


        

