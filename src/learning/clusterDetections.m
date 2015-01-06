% Cluster detected cars based on orientation and size

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


%% input

inPatchesDir = [CITY_DATA_PATH 'learning/cam572-sparse/patches/'];
inCarsDir = [CITY_DATA_PATH 'learning/cam572-sparse/cars/'];
goodListPath = [CITY_DATA_PATH 'learning/cam572-sparse/oneCarList.txt'];

clustersPath = [CITY_DATA_PATH 'violajones/patches/clusters.mat'];
load(clustersPath);


% read goodList
carsList = readList (goodListPath);


%% output

patchesDir = [CITY_DATA_PATH, 'violajones/patches/'];



if true

%% dislay size/oritenations of all cars

sizes = zeros(length(carsList), 1);
yaw = zeros(length(carsList), 1);
pitch = zeros(length(carsList), 1);
proportions = zeros(length(carsList), 1);

for i = 1 : length(carsList)
    % load car object
    clear car
    load ([inCarsDir carsList{i} '.mat']);
    
    sizes(i) = (car.bbox(3) + car.bbox(4)) / 2;
    proportions(i) = car.bbox(4) / car.bbox(3);
    yaw(i) = car.orientation(1);
    pitch(i) = car.orientation(2);
end

figure(1);
scatter (sizes, yaw);
title ('car distribution');
xlabel ('car size in pixels');
ylabel ('car YAW orientation in degrees');

figure(2);
scatter (sizes, pitch);
title ('car distribution');
xlabel ('car size in pixels');
ylabel ('car PITCH orientation in degrees');

end

%% cluster cars

iclusters = zeros(length(sizes), 1);
counters = zeros(length(clusters),1);

for i = 1 : length(carsList)
    for j = 1 : length(clusters)
        cluster = clusters(j);
        if yaw(i) > cluster.minyaw && yaw(i) <= cluster.maxyaw && ...
           sizes(i) > cluster.minsize && sizes(i) <= cluster.maxsize
              iclusters(i) = j;
              counters(j) = counters(j) + 1;
              break;
        end
    end
end

% write down patches

for i = 1 : max(iclusters(:))
    % make dirs
    clusterName = sprintf('pos-%02d/', i);
    if exist([patchesDir clusterName], 'dir')
        rmdir ([patchesDir clusterName], 's');
    end
    mkdir ([patchesDir clusterName])
    
    % write patches to dirs
    indices = find (iclusters == i);
    for j = 1 : length(indices)
        clear car
        load ([inCarsDir carsList{indices(j)} '.mat']);
        goast = car.goast;
        goast = imresize(goast, clusters(i).carsize);
        
        imageName = sprintf('%05d.png', j);
        imwrite (uint8(-goast / 2 + 127), [patchesDir clusterName imageName]);
    end
end

