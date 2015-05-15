% FrombackDetectorSql.m
% Use FrombackDetector class to detect cars in every image from a database
%

clear all

%% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input
db_in_file  = 'datasets/labelme/Databases/572-Nov28-10h-pair/init.db';
db_out_file = 'datasets/labelme/Databases/572-Nov28-10h-pair/detected/fromback-dr8.db';

video_file  = 'camdata/cam572/Nov28-10h.avi';
back_file   = 'camdata/cam572/Nov28-10h-back.png';

verbose = 0;


%% init

% copy input to output
safeCopyFile([CITY_DATA_PATH db_in_file], [CITY_DATA_PATH db_out_file]);

% geometry
load([CITY_DATA_PATH, 'models/cam572/GeometryObject_Camera_572.mat']);

% background
background = BackgroundGMM('pretrain_video_path', [CITY_DATA_PATH video_file]);

% detector
frombackDetector = FrombackDetector(geom, background);
frombackDetector.DensityRatio = 8.0;
%frombackDetector.DensitySigma = 1.3;
%frombackDetector.noFilter = true;

% back
backimage = imread([CITY_DATA_PATH back_file]);


%% work 

sqlite3.open([CITY_DATA_PATH db_out_file]);

imagefiles = sqlite3.execute('SELECT imagefile FROM images');

for i = 1 : length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    
    img = imread([CITY_DATA_PATH imagefile]);
    ghost = image2ghost(img, backimage);
    
    mask = background.subtract(img, 'denoise', false);

    tic
    cars = frombackDetector.detect(img);
    toc

    if verbose > 1
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
    
    for j = 1 : length(cars)
        car = cars(j);
        sqlite3.execute('INSERT INTO cars(imagefile,x1,y1,width,height) VALUES (?,?,?,?,?)', ...
            imagefile, car.bbox(1), car.bbox(2), car.bbox(3), car.bbox(4));
    end     
end


sqlite3.close()

