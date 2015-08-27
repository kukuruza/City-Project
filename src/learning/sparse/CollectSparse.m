% Collect patches seen by background detector
% Takes a original video, as well as ghost video on input
%   If background detector sees a very distinct spot, it becomes a car
%   Patch, ghost, orientation, size of the car is extracted
%
% Note: reason for using ghost video as opposed to ghost image
%       is the possibility to use varying illumination conditions
%       They are encoded in the video, but not the image.

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

% input
in_db_path  = [CITY_DATA_PATH 'datasets/unlabelled/Databases/541-Jul26-16h/init-ghost.db'];

% output
out_db_path = [CITY_DATA_PATH 'datasets/unlabelled/Databases/541-Jul26-16h/sparse-ghost.db'];

% for sparse dataset need strict parameters
DensitySigma = 2.5;   % effective radius around car to be empty
DensityRatio = 12.0;   % how much dense inside / sparse outside it should be

filter_by_sparsity = true;

write = false;
show = true;


%% work

% init matlab module which can detect rectangular blobs
blob = vision.BlobAnalysis(...
       'CentroidOutputPort', false, ...
       'AreaOutputPort', false, ...
       'BoundingBoxOutputPort', true, ...
       'MinimumBlobAreaSource', 'Property', ...
       'MinimumBlobArea', 50);

% open database
copyfile (in_db_path, out_db_path);
sqlite3.open (out_db_path);

% read imagefiles
imagefiles = sqlite3.execute('SELECT imagefile,maskfile FROM images');

for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    maskfile  = imagefiles(i).maskfile;
    img  = imread(fullfile(CITY_DATA_PATH, imagefile));
    mask = imread(fullfile(CITY_DATA_PATH, maskfile));
    assert (ismatrix(mask));
    assert (size(mask,1) == size(img,1) && size(mask,2) == size(img,2));
    
    
    bboxes = step(blob, mask);

    cars = Car.empty;
    for k = 1 : size(bboxes,1)
        cars(k) = Car(bboxes(k,:));
    end
    fprintf ('background cars: %d\n', length(cars));
    
        
    statuses = cell(length(cars),1);
    for j = 1 : length(cars)
        statuses{j} = 'ok';
    end
    if filter_by_sparsity
        statuses = filterBySparsity (mask, cars, statuses, 'verbose', show, ...
                         'DensitySigma', DensitySigma, 'DensityRatio', DensityRatio);
        indices = find(cellfun('isempty', strfind(statuses, 'ok')));
        cars (indices) = [];
        fprintf ('sparse cars:     %d\n', length(cars));
    end
    
    % TODO: write scores to db

    if ~isempty(cars) && write
        for j = 1 : length(cars)
            car = cars(j);
            bbox = car.bbox;
            query = 'INSERT INTO cars(imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?)';
            sqlite3.execute(query, imagefile, 'object', bbox(1), bbox(2), bbox(3), bbox(4));
        end
    end
    
    if show
        img_out = img;
        mask_out  = uint8(mask(:,:,[1,1,1])) * 255;
        for j = 1 : length(cars)
            mask_out    = cars(j).drawCar(mask_out, 'color', 'yellow', 'tag', 'detected');
            img_out   = cars(j).drawCar(img_out, 'color', 'yellow', 'tag', 'detected');
        end
        figure (1)
        subplot(1,2,1), imshow(mask_out);
        subplot(1,2,2), imshow(img_out);
        pause()
    end
end

sqlite3.close();
if ~write
    delete(out_db_path);
end



