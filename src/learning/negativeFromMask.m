% Learn car appearance models from data
%   If background detector sees a very distinct spot, it becomes a car
%   Patch, ghost, orientation, size of the car is extracted

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;



%% input

verbose = 0;
dowrite = true;

thresholdGray = 0;  % if ==0, then ignored

videoPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.avi'];
timestampPath = [CITY_DATA_PATH 'camdata/cam572/10am/2-hours.txt'];

clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];
load (clustersPath);



%% output
outClusterDir = [CITY_DATA_PATH 'violajones/patches/neg/'];




%% loading objects

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

if dowrite
    if exist(outClusterDir, 'dir')
        rmdir (outClusterDir, 's');
    end
    mkdir (outClusterDir)
end

for t = 1 : 1172
    
    % read image
    [frame, ~] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);

    % skip first 100 frames
    if t <= 100, continue, end
    
    % get the ghost of foreground. Cars will be learned from this.
    frame_ghost = int32(frame) - backImage;
    frame_ghost = uint8(frame_ghost / 2 + 128);

    if thresholdGray
        frame_ghost( abs(frame_ghost - 128) > thresholdGray ) = 128;
    end

    % subtract background and return mask
    mask = background.subtract(frame);
    
    if verbose > 0, figure(1), subplot(2,2,1), imshow(frame); title('original'); end
    if verbose > 1, figure(2), subplot(2,2,1), imshow(mask); title('foreground'); end
    
    mask_out = zeros(size(mask,1),size(mask,2));
    
    % work for every cluster separately
    for icluster = 3 : length(clusters)
        if mod(icluster,2) == 0, continue; end
        recall_mask1 = clusters(icluster).recallMask;
        recall_mask2 = clusters(icluster+1).recallMask;
        recall_mask = recall_mask1 | recall_mask2;
        
%        mask_cluster = mask & ~recall_mask;

        carsize = clusters(icluster).carsize;
        mask_big = imdilate (mask, strel('disk', floor(mean(carsize)/8)) );
        mask_small = imerode (mask_big, strel('disk', floor(mean(carsize)/3.5)) );
        mask_cluster = ~mask_small & recall_mask;
        
        mask_out = mask_out | mask_cluster;
        
        if verbose > 1, figure(2), subplot(2,2,floor(icluster/2+1)+1), imshow(mask_cluster); end
        if verbose > 2, figure(3), subplot(2,2,floor(icluster/2+1)+1), imshow(mask_big - mask_small); end
    end % iclusters

    if dowrite
        % ghost of the edge of the mask
        r = frame_ghost(:,:,1);
        g = frame_ghost(:,:,2);
        b = frame_ghost(:,:,3);
        r(~mask_out) = 0;
        g(~mask_out) = 0;
        b(~mask_out) = 0;
        frame_out = cat(3,r,g,b);
        
        %clusterName = sprintf('neg-%02d/', icluster);
        frame_path = [outClusterDir sprintf('f%04d.png',t)];
        imwrite(frame_out, frame_path);
    end

    if verbose > 0, figure(1), subplot(2,2,2), imshow(frame_out); end
    if verbose > 2, figure(3), subplot(2,2,1), imshow(mask_out); end
    if verbose > 0, pause; end
end

clear frameReader



