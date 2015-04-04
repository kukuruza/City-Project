clear all
size_map = imread('additionals/578_roadmap.tiff');

% extract edges from the size map
% edges_map -- has values 0 (background), 
%                         255 (edge), 
%                         128 (edge for which yawOnEdges should not be called)
% roi_mask  -- might be smaller than (size_map > 0)
[edges_map, roi_mask] = mask2edges(size_map, 'MinSize', 5);

% find yaw on edges
yaw_map = yawOnEdges (edges_map == 255, 'NeighborhoodSize', 7, 'DilateEdge', 0, 'verbose', 0);

% interpolate yaw in the whole road area
ThreshTest = 0.05;      % very coarse, for testing only
ThreshDeploy = 0.0001;  % accurate enough
yaw_map = roadSoapFilm (yaw_map, edges_map, 'Thresh', ThreshTest, 'verbose', 1);
yaw_map(~roi_mask) = 0;

% adjust for direction
direction_map = (imread('additionals/578_directionmap.tiff') > 0);
direction_mask = direction_map & roi_mask;
yaw_map (direction_mask) = yaw_map(direction_mask) + 180;

imagesc(yaw_map);
imwrite(uint16(yaw_map + 360), 'additionals/578_yawmap.tiff')
