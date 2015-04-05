clear all
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;


%% input

camname = 'cam671';

ThreshTest = 0.1;       % very coarse, for testing only
ThreshDeploy = 0.0001;  % accurate enough
thresh = ThreshDeploy;  % assign here!

% verbose = 0 -- shows only the final result
%           1 -- shows the process of filling in values
%           2 -- has waitforbuttonpress on intermediate images
verbose = 1;


%% work. Dont change without need

size_map_path      = fullfile(CITY_DATA_PATH, 'models', camname, 'mapSize.tiff');
direction_map_path = fullfile(CITY_DATA_PATH, 'models', camname, 'mapDirection.tiff');
yaw_map_path       = fullfile(CITY_DATA_PATH, 'models', camname, 'mapYaw.tiff');

size_map = imread(size_map_path);
imshow(size_map)

% extract edges from the size map
% edges_map -- has values 0 (background), 
%                         255 (edge), 
%                         128 (edge for which yawOnEdges should not be called)
% roi_mask  -- might be smaller than (size_map > 0)
[edges_map, mask] = mask2edges(size_map, 'MinSize', 10, 'Type', 'Sobel', 'verbose', verbose);
imshow(edges_map)

% find yaw on edges
yaw_map = yawOnEdges (edges_map == 255, 'NeighborhoodSize', 7, 'DilateEdge', 0, 'verbose', verbose);
imagesc(yaw_map);

% interpolate yaw in the whole road area
colormap default
yaw_map = roadSoapFilm (yaw_map, edges_map, 'Thresh', thresh, 'verbose', verbose);
yaw_map(~mask) = 0;
imagesc(yaw_map);

% adjust for direction
direction_map = imread(direction_map_path) > 0;
direction_mask = direction_map & mask;
yaw_map (direction_mask) = yaw_map(direction_mask) + 180;

% display and save (saved as angle = degree % 360)
imagesc(yaw_map);
imwrite(uint16(mod(yaw_map, 360)), yaw_map_path)
