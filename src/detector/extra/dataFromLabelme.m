% this script loads the labelme database, and extracts all car patches
%

% out background is always road. So let's put the cars on that color
BackGroundColor = 128;
bh = 3;
bw = 5;
height = 60;
width = 80;

REMOTEIMAGES = 'http://people.csail.mit.edu/brussell/research/LabelMe/Images';
REMOTEANNOTATIONS = 'http://people.csail.mit.edu/brussell/research/LabelMe/Annotations';

CarFilter = 'car+front-occluded-crop,car+frontal-occluded-crop';

DirCropped = '/Volumes/Other/projects/City-Project/data/Labelme/croppedFront90x46b/';

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

%database_path = 

%database = LMdatabase (REMOTEANNOTATIONS);
%load (database_path);


% % First create the list of images that you want:
% Dcar = LMquery(D, 'object.name', 'car', 'word');
% clear folderlist filelist
% for i = 1:length(Dcar)
%       folderlist{i} = Dcar(i).annotation.folder;
%       filelist{i} = Dcar(i).annotation.filename;
% end
% 
% % Install the selected images:
% LOCALIMAGES = '/Volumes/Other/projects/City-Project/data/Labelme/Images';
% LOCALANNOTATIONS = '/Volumes/Other/projects/City-Project/data/Labelme/Annotations';
% LMinstall (folderlist, filelist, LOCALIMAGES, LOCALANNOTATIONS);

%D = LMquery(Dcar, 'object.name', CarFilter);

counter = 0;
for i = 1 : length(Dcar)
    [annotation, img] = LMread(D, i, LOCALIMAGES);
%     [mask, class] = LMobjectmask(annotation, LOCALIMAGES);
%     binaryMask = ~logical(sum(mask, 3));
%     if ndims(img) == 3
%         binaryMask = cat(3, binaryMask, binaryMask, binaryMask);
%     end  
%     img (binaryMask) = BackGroundColor;

    for k = 1 : length(D(i).annotation.object)
        imgCrop = LMobjectnormalizedcrop (img, D(i).annotation, k, ...
                                          [bh bw], height, width, BackGroundColor);
        D(i).annotation.object(k).name
        filepath = [DirCropped, sprintf('patch%06d.png', counter)];
        imwrite (imgCrop, filepath);
        counter = counter + 1;
    end
end
    