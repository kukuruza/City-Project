% Use a detector to detect cars in every image from a database
%

clear all
sqlite3.close();

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

% databases
in_db_path  = fullfile(CITY_DATA_PATH, 'databases/labelme/572-Oct30-17h-pair/init-image.db');
out_db_path = fullfile(CITY_DATA_PATH, 'databases/labelme/572-Oct30-17h-pair/detected/VOC0712_vgg_16layers.db');

% input
model_dir = fullfile(getenv('FASTERRCNN_ROOT'), 'output/faster_rcnn_final/faster_rcnn_VOC0712_vgg_16layers');

% what to do
write = true;
show = false;



%% init

% copy input to output
safeCopyFile (in_db_path, out_db_path);
sqlite3.open (out_db_path);
if write
    % just in case
    sqlite3.execute('DELETE FROM matches');
    sqlite3.execute('DELETE FROM cars');
end

% image reader backend
imgReader = ImgReaderVideo();

% detector
detector = FasterRcnnDetector(model_dir, 'use_gpu', true);
%detector = FrombackDetector();

% features file
assert (strcmp(out_db_path(end-2:end), '.db'));
features_path = [out_db_path(1:end-3), '.txt'];
if exist(features_path, 'file')
    delete(features_path);
end


%% work 


imagefiles = sqlite3.execute('SELECT imagefile FROM images');

for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;

    maskfile = sqlite3.execute('SELECT maskfile FROM images WHERE imagefile = ?', imagefile);

    img  = imgReader.imread(imagefile);
    mask = imgReader.maskread(maskfile.maskfile);
    
    tic
    %cars = detector.detect(img);
    [cars, features] = detector.detect(img, mask);
    %features = rand(length(cars), 10);
    toc

    if show
        cmap = colormap('Autumn');
        for j = 1 : length(cars)
            car = cars(j);
            img = car.drawCar(img);
        end
        imshow([mask2rgb(mask), img]);
        waitforbuttonpress
    end
    
    if write
        for j = 1 : length(cars)
            car = cars(j);
            s = 'INSERT INTO cars(imagefile,name,score,x1,y1,width,height) VALUES (?,?,?,?,?,?,?)';
            sqlite3.execute(s, imagefile, car.name, car.score, car.bbox(1), car.bbox(2), car.bbox(3), car.bbox(4));
        end
        
        dlmwrite(features_path, features, '-append');
    end
end

sqlite3.close();

