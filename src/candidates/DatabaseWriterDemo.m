% Save the candidates into a database using the database writer
% Demo for DataabaseWriter for all the features

clear all;

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script


%% input

% What to do
write = false;
show = true;

% Setting up the paths for input and reference database
dbPath = fullfile(CITY_DATA_PATH, 'candidates', '572-Oct30-17h-pair_selective.db');
%dbPath = fullfile(CITY_DATA_PATH, 'candidates', '572-Oct30-17h-pair_sizemap.db');
refPath = fullfile(CITY_DATA_PATH, 'datasets/labelme/Databases/572-Oct30-17h-pair/init-ghost.db');

% Size map
sizeMapPath = fullfile(CITY_DATA_PATH, 'models/cam572/', 'mapSize.tiff');


%% Work

% Creating a simple DatabaseWriter instance
if write
    writer = DatabaseWriter(dbPath, refPath);
end

% Size map
mapSize = imread(sizeMapPath);

% Reading the image listing from the db
dbRefId = sqlite3.open(refPath);
imagefiles = sqlite3.execute(dbRefId, 'SELECT imagefile FROM images');
fprintf('found %d frames in the db.\n', length(imagefiles));

% Candidates object
%cands = CandidatesSizemap (mapSize);
cands = CandidatesSelectSearch('mapSize', mapSize);
    
for i = 1:length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    
    % Reading the ghost
    image = imread (fullfile(CITY_DATA_PATH, imagefile));
    
    % Getting the candidates
    %bboxes = cands.getCandidates();
    bboxes = cands.getCandidates('image', image);

    % Get the mask
    query = 'SELECT maskfile FROM images WHERE imagefile = ?';
    maskfile = sqlite3.execute(dbRefId, query, imagefile);
    mask = imread(fullfile(CITY_DATA_PATH, maskfile.maskfile));
    assert (ismatrix(mask));
    
    % Get the candidates filtered by mask
    fildtersBboxes = cands.filterCandidatesBackground (bboxes, mask);
    
    if show
        debugImg = cands.drawCandidates(fildtersBboxes, image);
        imshow([debugImg 255*mask(:,:,[1,1,1])]);
        pause();
    end
    
    % Writing the candidates
    if write
        writer.saveBoxesToDatabase(fildtersBboxes, imagefile, 'candidate');
    end
    
    fprintf('%s: %d candidates\n', imagefile, size(fildtersBboxes,1));
end

% Closing the database / DatabaseWriter
sqlite3.close(dbRefId);
if write
    writer.closeDatabase();
end
