% 
%

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

%% input and ground truth

% input images
imDir = [CITY_DATA_PATH 'testdata/detector/detections'];
imPath{1} = [imDir '002.png'];
imPath{2} = [imDir '003.png'];
imPath{3} = [imDir '004.png'];
imPath{4} = [imDir '005.png'];
imPath{5} = [imDir '006.png'];
imPath{6} = [imDir '007.png'];
imPath{7} = [imDir '008.png'];
imPath{8} = [imDir '009.png'];
imPath{9} = [imDir '010.png'];
imPath{10} = [imDir '011.png'];
imPath{11} = [imDir '012.png'];
imPath{12} = [imDir '013.png'];
imPath{13} = [imDir '014.png'];
imPath{14} = [imDir '015.png'];
imPath{15} = [imDir '016.png'];
imPath{16} = [imDir '017.png'];
imPath{17} = [imDir '018.png'];
imPath{18} = [imDir '019.png'];
imPath{19} = [imDir '020.png'];

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

for iframe = 1 : length(imPath)   
    % read frame
    frame = imread(imPath{iframe});
    j = iframe;
    cars = Car.empty;
    
    file = strcat('00', num2str(iframe+1));
    save(fileGeoProb, 'ProbGeo');
    
    
    for i = 1:length(imPath)
        cars(i) = Car(bboxes{j}(i, :));
    end
    
    %In order to read the patch for the ith car
    % cars{i}.features
    % in order to read the bbox
    % cars{i}.bbox
    
    % counting the new cars and total number of cars for a new frame

        counting.Th = 0.5;
        counting.WeightGeom = 0.4;
        counting.WeightHog = 0.2;
        counting.WeightCol = 0.4;
        [newCarNumber Match] = counting.processFrame(frame, cars);  % cars is the cell array of the class carappearance, every cell is the carappearance based on every bbox
    
    Result{counting.framecounter - 1} = Match;
    % counting.framecounter = counting.framecounter + 1;
    %     count1 = count0 + newCarNumber;    % count1 is the total number of cars for all the frames.
    %     count0 = count1;    
end
    % compare output with ground truth
    % corresp{iframe}
    
    
    
        for iframe = 1 : length(bboxes)
            if(iframe> 1)
                t = (Result{iframe}== corresp{iframe});  % true matrix for iframe
                f = (Result{iframe}~= corresp{iframe});
                tt(iframe-1) = sum(sum(t));              % tt vector is the total true value for all frames 
                ff(iframe-1) = sum(sum(f));
                trueMatrix{iframe-1} = t;                 % trueMatrix cell array is the true matrix for all iframes
                falseMatrix{iframe-1} = f;
                % Truth = sum(tt,1);           
                % False = sum(ff,1);
            end
        end
        
    
%     save('Result', 'Result');
%     save('trueMatrix', 'trueMatrix');
%     save('falseMatrix', 'falseMatrix');
%     save('T-all-frames', 'tt');
%     save('F-all-frames', 'ff');

     
     
     
   