% save positiveInstancesFront either as a set of patches or as an info file
%   for opencv training

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

run '../../rootPathsSetup.m';
run '../../subdirPathsSetup.m'

outInfoFile = [CITY_LOCAL_DATA_PATH,  'violajones/cameras/cam572/cam572_pos.txt'];
relativeImageDir = '../../../2-hours/camera572/';
outPatchesDir = [CITY_LOCAL_DATA_PATH,  'violajones/cameras/cam572/positive_matlab/'];

%counter = 0;

fid = fopen(outInfoFile, 'w');

for i = 1 : length(positiveInstancesFront)
    instance = positiveInstancesFront(i);
    numBoxes = size(instance.objectBoundingBoxes,1);
    img = imread(instance.imageFilename);
    [~, imgName, ext] = fileparts(instance.imageFilename);
    fprintf (fid, '%s %d ', [relativeImageDir, imgName, ext], numBoxes);
    for j = 1 : numBoxes
        bbox = instance.objectBoundingBoxes(j,:);
        %patch = img(bbox(2) : bbox(2)+bbox(4)-1, bbox(1) : bbox(1)+bbox(3)-1);
        %imwrite (patch, [outPatchesDir num2str(counter) '.png']);
        %counter = counter + 1;
        fprintf (fid, ' %d %d %d %d ', bbox);
    end
    fprintf(fid, '\n');
end

fclose(fid);
