% Write pairs of frames for Amazon Mech Turk
%

clear all


%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
run (fullfile(getenv('CITY_PATH'), 'src/subdirPathsSetup.m'));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input
videoPath = [CITY_DATA_PATH 'camdata/cam572/Oct30-17h.avi'];
backPath  = [CITY_DATA_PATH 'camdata/cam572/Oct30-17h-back.png'];

dir_name = '572-Oct30-17h-frame';
db_name = 'init.db';

beginFrame = 100;
endFrame = 200;
betweenFrame = 2;

makePairs = false;




%% init
dataset_dir = 'datasets/labelme/';
assert (exist ([CITY_DATA_PATH dataset_dir], 'dir') == 7);

db_dir = [CITY_DATA_PATH dataset_dir 'Databases/' dir_name];
im_dir = [CITY_DATA_PATH dataset_dir 'Images/' dir_name];
gh_dir = [CITY_DATA_PATH dataset_dir 'Ghosts/' dir_name];
ma_dir = [CITY_DATA_PATH dataset_dir 'Masks/' dir_name];
pa_dir = [CITY_DATA_PATH dataset_dir 'Pairs/' dir_name];
if exist(db_dir, 'dir'), rmdir(db_dir, 's'); end; mkdir(db_dir);
if exist(im_dir, 'dir'), rmdir(im_dir, 's'); end; mkdir(im_dir);
if exist(gh_dir, 'dir'), rmdir(gh_dir, 's'); end; mkdir(gh_dir);
if exist(ma_dir, 'dir'), rmdir(ma_dir, 's'); end; mkdir(ma_dir);
if exist(pa_dir, 'dir') && makePairs, rmdir(pa_dir, 's'); end; mkdir(pa_dir);
dir_name = [dir_name '/'];

frameReader = FrameReaderVideo (videoPath);

% background
load ([CITY_DATA_PATH 'models/cam572/backgroundGMM.mat']);
pretrainBackground (background, videoPath);
backimage = imread (backPath);

% output database
dbpath = [db_dir '/' db_name];
dbCreate(dbpath);
sqlite3.open(dbpath);

% output of amazon
if makePairs
    frameWriter = FrameWriterImpairs (pa_dir);
end



% skip frames
for t = 0 : beginFrame-1    
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('skipped frame: %d\n', t);
end

for t = beginFrame : endFrame-1
    
    [frame, timestamp] = frameReader.getNewFrame();
    if isempty(frame), break, end
    fprintf ('frame: %d\n', t);
    
    % extract ghost and mask
    ghost = uint8((int32(frame) - int32(backimage)) / 2 + 128);
    mask = background.subtract(frame);
    
    % im_name = sprintf ('%04d', t);
    % TODO: should NOT be +1. It is for compatibility
    im_name = sprintf ('%06d', t-100);
    
    % save image pairs
    if makePairs == true
        frameWriter.writeNextFrame (frame, im_name);
    end

    % save different images
    image_file = [dataset_dir 'Images/' dir_name im_name '.jpg'];
    ghost_file = [dataset_dir 'Ghosts/' dir_name im_name '.jpg'];
    mask_file =  [dataset_dir 'Masks/'  dir_name im_name '.png'];
    imwrite (frame, [CITY_DATA_PATH image_file]);
    imwrite (ghost, [CITY_DATA_PATH ghost_file]);
    imwrite (mask,  [CITY_DATA_PATH mask_file]);

    % add to db
    width  = size(frame, 2);
    height = size(frame, 1);
    time_db = matlab2dbTime(timestamp);
    sqlite3.execute('INSERT INTO images VALUES (?,?,?,?,?,?,?)', ...
         image_file, dir_name, width, height, ghost_file, mask_file, time_db);
    
    
    for j = 1 : betweenFrame
        frame = frameReader.getNewFrame();
        if isempty(frame), break, end
    end
end

clear frameReader
clear frameWriter
sqlite3.close();


