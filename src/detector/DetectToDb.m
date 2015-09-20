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
in_db_path  = fullfile(CITY_DATA_PATH, 'databases/labelme/572-Nov28-10h-pair/init-image.db');
out_db_path = fullfile(CITY_DATA_PATH, 'databases/labelme/572-Nov28-10h-pair/VOC0712_vgg_16layers.db');

% input
%mapSize_path = 'models/cam572/mapSize.tiff';

% what to do
write = true;
show = false;



%% init

% size map
%size_map = imread(fullfile(CITY_DATA_PATH, mapSize_path));

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
detector = FasterRcnnDetector();
%detector = FrombackDetector(size_map);


%% work 


imagefiles = sqlite3.execute('SELECT imagefile FROM images');

for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;

    maskfile = sqlite3.execute('SELECT maskfile FROM images WHERE imagefile = ?', imagefile);

    img  = imgReader.imread(imagefile);
    mask = imgReader.maskread(maskfile.maskfile);
    
    tic
    cars = detector.detect(img);
    %cars = detector.detect(img, mask);
    toc

    if show
        cmap = colormap('Autumn');
        for j = 1 : length(cars)
            car = cars(j);
            colorindex = floor(car.score * size(cmap,1)) + 1;
            color = cmap (colorindex, :) * 255;
            img = car.drawCar(img, 'color', color);
        end
        imshow([mask2rgb(mask), img]);
        waitforbuttonpress
    end
    
    if write
        for j = 1 : length(cars)
            car = cars(j);
            s = 'INSERT INTO cars(imagefile,name,x1,y1,width,height) VALUES (?,?,?,?,?,?)';
            sqlite3.execute(s, imagefile, 'detected', car.bbox(1), car.bbox(2), car.bbox(3), car.bbox(4));
        end
    end
end

sqlite3.close();

