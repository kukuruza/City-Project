function GetAzimuthMap (in_lane_template)
% Given several files with maps of lanes, generate a map of azimuths
% Each file with lane maps must have one or more lines in the lane middles
% Output is just one png file with the map of azimuth angles, and alpha ch.
% Zero azimuth is North (to min Y), 90 degrees is East (to max X)
% Azimuth is written in DEGREES, DIVIDED BY 2 in order to fit into [0, 255]
% This file know all conventions about png and alpha and so on
%
% args:
%   in_lane_template:   wildcard template of all lane files,
%                       e.g. 'augmentation/scenes/cam124/google1/lane*.png'

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input

% input
in_lane_template = [CITY_DATA_PATH in_lane_template];

% output
out_angles_path = fullfile (fileparts(in_lane_template), 'azimuth.png');
out_lanes_path  = fullfile (fileparts(in_lane_template), 'lanes.json');

% verbose == 0:  basic printout
%         == 1:  show plot for each segment in each file
%         == 2:  debug: show filters, directions, etc
verbose = 0;

% what to do
write = true;
show = true;



%% compute

% init empty array of lanes
lanes0 = repmat(struct('length',0,'N',0,'x',[],'y',[],'azimuth',[]), 0);

% for each file that matches the pattern
clear azimuths0 mask0
lane_names = dir(in_lane_template);
assert (~isempty(lane_names))
for i = 1 : length(lane_names)
    fprintf ('lanes file name: %s.\n', lane_names(i).name);
    lane_path = fullfile (fileparts(in_lane_template), lane_names(i).name);

    [im,~,alpha] = imread (lane_path);
    im = rgb2gray(im);
    im = double(im);

    % convention to have lanes on black background, without alpha
    assert (min(alpha(:)) == 255);  % this means, alpha does not exist

    % create output var on the first iteration
    if ~exist('azimuths0','var'), azimuths0 = zeros(size(im)); end
    if ~exist('mask0','var'),     mask0 = false(size(im)); end
    
    % workhorse
    [azimuths, mask, lanes] = lanes2azimuth(im, 'verbose', verbose, ...
                                            'MinPoints4Fitting', 20.0);
    azimuths0 = azimuths0 + double(~mask0) .* azimuths;
    mask0 = mask0 | mask;
    lanes0 = [lanes0 lanes];
end

assert (all(all(azimuths0 >= 0 & azimuths0 <= 360)));

if show
    imagesc (azimuths0, [0, 360]);
end
if write
    % we'll write half precision to fit into uint8 [0, 255]
    azimuths0 = azimuths0 / 2;
    assert (all(all(azimuths0 >= 0 & azimuths0 <= 255)));
    out = uint8 (azimuths0(:,:,[1,1,1]));
    imwrite (out, out_angles_path, 'Alpha', double(mask0));
    savejson('', lanes0, struct('FileName',out_lanes_path));
end

end
