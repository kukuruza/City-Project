function inspectMatches (folder, varargin)
% inspectMatches car matches, produced by analyzePairs.py

global CITY_DATA_PATH
labelme_data_path = [CITY_DATA_PATH 'labelme/'];
assert (ischar(labelme_data_path))

% validate input
parser = inputParser;
addRequired(parser, 'folder', ...
    @(x) ischar(x) && exist(fullfile(labelme_data_path, 'Images', folder), 'dir'));
parse (parser, folder, varargin{:});


image_dir = fullfile (labelme_data_path, 'Images', folder);
images_pathlist = dir (fullfile(image_dir, '*.jpg'));

for i = 1 : length(images_pathlist)
    
    % read image
    image_path = fullfile(image_dir, images_pathlist(i).name);
    img = imread(image_path);
    
    % read cars
    [~, name, ~] = fileparts (images_pathlist(i).name);
    cars_dir = fullfile (labelme_data_path, 'Cars', folder);
    cars_pathlist = dir(fullfile(cars_dir, [name '-*.mat']));
    
    for j = 1 : length(cars_pathlist)
        carpair_path = fullfile(cars_dir, cars_pathlist(j).name);
        clear cars
        load (carpair_path)
        
        % logic in pair processing
        % for now, just TWO cars
        assert (mod(size(img,1), 2) == 0);
        halfheight = size(img,1) / 2;
        assert (length(cars) == 2);
        if cars(2).isOk()
            cars(2).bbox(2) = cars(2).bbox(2) + halfheight;
        end
        
        % remove if invalid
        assert (cars(1).isOk() || cars(2).isOk());
        if ~cars(2).isOk(), cars(2) = []; end
        if ~cars(1).isOk(), cars(1) = []; end
    
        % draw a pair
        imgdisp = drawCars(img, cars);
        imshow(imgdisp)
        pause ()
    end
    
end
