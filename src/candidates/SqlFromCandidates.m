% Go througb images and generate candidate regions to classify as car / not
% The result is saved as SQL

clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

verbose = true;
do_write = true;

dataset_dir = 'datasets/labelme';
dir_name = '572-Oct30-17h-pair';

mapsize_path = 'models/cam572/mapSize.tiff';

db_in_name  = 'init.db';
db_out_name = 'selsearch.db';

patch_size = [30, 40];
patch_dir = 'clustering/572-Oct30-17h-pair/selsearch';


%% init

db_dir = fullfile(CITY_DATA_PATH, dataset_dir, 'Databases', dir_name);
im_dir = fullfile(CITY_DATA_PATH, dataset_dir, 'Images', dir_name);
gh_dir = fullfile(CITY_DATA_PATH, dataset_dir, 'Ghosts', dir_name);

db_in_path  = fullfile(db_dir, db_in_name);
db_out_path = fullfile(db_dir, db_out_name);

imagenames = dir(fullfile(im_dir, '*.jpg'));

mapsize = imread(fullfile(CITY_DATA_PATH, mapsize_path));

cands = CandidatesSelectSearch('mapSize', mapsize);

% copy db_in_path to db_out_path and remove all cars
if do_write
    copyfile(db_in_path, db_out_path, 'f'); 
    sqlite3.open (db_out_path);
    sqlite3.execute('DELETE FROM cars');
    sqlite3.close();
    sqlite3.open (db_out_path);
end


%% work
carid = 0;

for t = 1 : length(imagenames)
    
    imagefile = fullfile(dataset_dir, 'Images', dir_name, imagenames(t).name);
    
    % read image
    ghost = imread(fullfile(gh_dir, imagenames(t).name));
    fprintf ('image: %s\n', imagenames(t).name);
    
    % get candidates
    bboxes = cands.getCandidates('image', ghost);
    fprintf ('num candidates: %d\n', size(bboxes,1));
    
    % TODO: write scores to db
    
    if ~isempty(bboxes) && do_write
        % write candidate into db
        for i = 1 : size(bboxes,1)
            bbox = bboxes(i,:);
            query = 'INSERT INTO cars(id,imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?,?)';
            sqlite3.execute(query, carid, imagefile, 'candidate', bbox(1), bbox(2), bbox(3), bbox(4));

            % get patch of this candidate
            patch_name = sprintf ('%08d.png', carid);
            patch_path = fullfile(CITY_DATA_PATH, patch_dir, patch_name);
            roi = bbox2roi(bbox);
            patch = ghost(roi(1) : roi(3), roi(2) : roi(4), :);
            patch = imresize(patch, patch_size, 'bilinear');
            imwrite(patch, patch_path);

            carid = carid + 1;
        end
    end
    
    
%     if verbose > 0
%         frame_out = image;
%         mask_out  = uint8(mask(:,:,[1,1,1])) * 255;
%         for j = 1 : length(cars)
%             mask_out    = cars(j).drawCar(mask_out, 'color', 'yellow', 'tag', 'detected');
%             frame_out   = cars(j).drawCar(frame_out, 'color', 'yellow', 'tag', 'detected');
%         end
%         figure (1)
%         subplot(2,2,1), imshow(mask_out);
%         subplot(2,2,2), imshow(ghost);
%         subplot(2,2,3), imshow(frame_out);
%         pause()
%     end
end


if do_write
    sqlite3.close();
end



