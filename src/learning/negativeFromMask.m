% Learn car appearance models from data
%   If background detector sees a very distinct spot, it becomes a car
%   Patch, goast, orientation, size of the car is extracted

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;



%% input

verbose = 0;
dowrite = true;

videoPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.avi'];
timestampPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.txt'];

clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];
load (clustersPath);

% geometry
cameraId = 572;
image = imread([CITY_SRC_PATH 'geometry/cam572.png']);
matFile = [CITY_SRC_PATH 'geometry/' sprintf('Geometry_Camera_%d.mat', cameraId)];
geom = GeometryEstimator(image, matFile);
sizeMap = geom.getCameraRoadMap();



%% output
outDir = [CITY_DATA_PATH 'violajones/patches/'];




%% init

% frame reader
frameReader = FrameReaderVideo (videoPath, timestampPath);

% background
load ([CITY_DATA_PATH, 'camdata/cam572/10am/models/backgroundGMM.mat']);

% true background
backImage = int32(imread([CITY_DATA_PATH, 'camdata/cam572/10am/background1.png']));

% geometry
cameraId = 572;
image = imread([CITY_SRC_PATH 'geometry/cam572.png']);
matFile = [CITY_SRC_PATH 'geometry/' sprintf('Geometry_Camera_%d.mat', cameraId)];
geom = GeometryEstimator(image, matFile);

sizeMap = geom.getCameraRoadMap();
orientationMap = geom.getOrientationMap();



%% work

% make dirs
for icluster = 1 : length(clusters)
    if dowrite && mod(icluster, 2) == 1
        clusterName = sprintf('neg-%02d/', icluster);
        if exist([outDir clusterName], 'dir')
            rmdir ([outDir clusterName], 's');
        end
        mkdir ([outDir clusterName])
    end
end
        
for t = 1 : 1172
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % skip first 100 frames
    if t <= 100, continue, end
    
    % get the trace of foreground. Cars will be learned from this.
    frame_goast = int32(frame) - backImage;

    % subtract background and return mask
    mask = background.subtract(frame);
    
    % mask of the whole road area
%     mask_road = sizeMap > 0;
    
    if verbose > 0, figure(1), subplot(2,2,1), imshow(frame); title('original'); end
    if verbose > 1, figure(2), subplot(2,2,1), imshow(mask); title('foreground'); end
%     if verbose > 1, figure(3), subplot(2,2,1), imshow(mask_road); title('road'); end
    
    % work for every cluster separately
    for icluster = 1 : length(clusters)
        if mod(icluster,2) == 0, continue; end
        recall_mask1 = clusters(icluster).recallMask;
        recall_mask2 = clusters(icluster+1).recallMask;
        recall_mask = recall_mask1 | recall_mask2;
        
        mask_cluster = mask & ~recall_mask;
        frame_cluster = frame_goast;

        % goast of the edge of the mask
        r = frame_cluster(:,:,1);
        g = frame_cluster(:,:,2);
        b = frame_cluster(:,:,3);
        r(~mask_cluster) = 0;
        g(~mask_cluster) = 0;
        b(~mask_cluster) = 0;
        frame_cluster = cat(3,r,g,b);

        frame_cluster = uint8(frame_cluster / 2 + 128);
        
        if dowrite
            clusterName = sprintf('neg-%02d/', icluster);
            frame_path = [outDir clusterName sprintf('f%04d.png',t)];
            imwrite(frame_cluster, frame_path);
        end
        if verbose > 0, figure(1), subplot(2,2,floor(icluster/2+1)+1), imshow(frame_cluster); end
        if verbose > 1, figure(2), subplot(2,2,floor(icluster/2+1)+1), imshow(mask_cluster); end
        if verbose > 1, figure(3), subplot(2,2,floor(icluster/2+1)+1), imshow(recall_mask); end
    end % iclusters

    if verbose > 0, pause; end
end

clear frameReader



