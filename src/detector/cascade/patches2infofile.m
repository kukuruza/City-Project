% create list of images and bboxes taking the whole patch

clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'

inImgDir = [CITY_LOCAL_DATA_PATH, 'violajones/cameras/cam572/positive_matlab/'];
outInfoPath = [CITY_LOCAL_DATA_PATH, 'violajones/opencv/man_fl.info'];
relativeImgDir = '../cameras/cam572/positive_matlab/';

imgNames = dir([inImgDir, '*.png']);


fid = fopen(outInfoPath, 'w');

for i = 1 : length(imgNames)
    imgPath = [inImgDir, imgNames(i).name];
    img = imread(imgPath);
    height = size(img,1);
    width = size(img,2);
    relPath = [relativeImgDir, imgNames(i).name];
    fprintf (fid, '%s 1  %d %d %d %d \n', relPath, 1, 1, width, height);
end

fclose(fid);
