load('camera360.mat')

info=labelingSession.ImageSet.ImageStruct;

num = length(info);
numBbox = 0;
numFore = 0;
inx = [32, 31, 30, 29, 22, 21, 20, 19, 47, 55];

workingDir = '/Users/lgui/Dropbox/City-Project/data/2-min';
resultDir = fullfile(workingDir,'Result');

for i = 1:num
    imgName = info(i).imageFilename;
    bbox = info(i).objectBoundingBoxes;
%     im=imread(imgName);
%     imshow(im)
    cen = [bbox(:,1)+floor(bbox(:,3)/2),bbox(:,2)+floor(bbox(:,4)/2)]; 
    
    mname = sprintf('result%d.jpg',inx(i));
    maskname = fullfile(resultDir,mname);
    
    im = imread(maskname);
    [m,~]=size(bbox);
    for j = 1:m
        if im(cen(j,2),cen(j,1))==255
            numFore = numFore +1;
        end
    end
    numBbox = numBbox + m;
end

recall = numFore / numBbox;