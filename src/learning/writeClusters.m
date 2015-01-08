% Write information about clusters into an array of structures and save
%

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


%% input

verbose = 1;

% geometry
cameraId = 572;
image = imread([CITY_SRC_PATH 'geometry/cam572.png']);
matFile = [CITY_SRC_PATH 'geometry/' sprintf('Geometry_Camera_%d.mat', cameraId)];
geom = GeometryEstimator(image, matFile);

sizeMap = geom.getCameraRoadMap();
orientationMap = geom.getOrientationMap();


%% output
clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];




clusters(1) = struct('minyaw', -180, 'maxyaw', -90, 'minsize', 20, 'maxsize', 40, 'carsize', [15 20]);
clusters(2) = struct('minyaw', -90,  'maxyaw', 0, 'minsize', 20, 'maxsize', 40, 'carsize', [15 20]);
clusters(3) = struct('minyaw', -180, 'maxyaw', -90, 'minsize', 40, 'maxsize', 100, 'carsize', [30 40]);
clusters(4) = struct('minyaw', -90,  'maxyaw', 0, 'minsize', 40, 'maxsize', 100, 'carsize', [30 40]);
clusters(5) = struct('minyaw', -180, 'maxyaw', -90, 'minsize', 100, 'maxsize', 1000, 'carsize', [75 100]);
clusters(6) = struct('minyaw', -90,  'maxyaw', 0, 'minsize', 100, 'maxsize', 1000, 'carsize', [75 100]);

minsizeTolerance = 0.9;
maxsizeTolerance = 1;
seDilate = strel('disk', 25);  % maybe better to do that on rectified mask


for i = 1 : length(clusters)
    cluster = clusters(i);
    mask = sizeMap >  cluster.minsize * minsizeTolerance & ...
           sizeMap <= cluster.maxsize * maxsizeTolerance & ...
           orientationMap.yaw > cluster.minyaw & orientationMap.yaw <= cluster.maxyaw;
    mask = imdilate(mask, seDilate);
    clusters(i).recallMask = mask;
    if verbose, imshow(mask); pause; end
end

save (clustersPath, 'clusters');
