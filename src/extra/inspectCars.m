function inspectCars (folder, varargin)
% inspectMatches car matches, produced by analyzeFrames.py

global CITY_DATA_PATH
labelme_data_path = [CITY_DATA_PATH 'labelme/'];
assert (ischar(labelme_data_path))

% validate input
parser = inputParser;
addRequired(parser, 'folder', ...
    @(x) ischar(folder) && exist(fullfile(labelme_data_path, 'Images', folder), 'dir'));
parse (parser, folder, varargin{:});


image_dir = fullfile (labelme_data_path, 'Images', folder);
images_pathlist = dir (fullfile(image_dir, '*.jpg'));

for i = 1 : length(images_pathlist)
    
    % read image
    image_path = fullfile(image_dir, images_pathlist(i).name);
    img = imread(image_path);
    
    % read cars
    clear cars
    [~, name, ~] = fileparts (images_pathlist(i).name);
    cars_path = fullfile (labelme_data_path, 'Cars', folder, [name '.mat']);
    load (cars_path)
    
    imgdisp = drawCars(img, cars);
    imshow(imgdisp)
    pause ()
    
end
