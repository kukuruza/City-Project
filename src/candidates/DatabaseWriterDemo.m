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
show = false;

% Setting up the paths for input and reference database
%dbPath = fullfile(CITY_DATA_PATH, 'candidates', '671-Mar24-12h_selective.db');
dbPath = fullfile(CITY_DATA_PATH, 'candidates', '671-Mar24-12h_sizemap.db');
refPath = fullfile(CITY_DATA_PATH, 'datasets/sparse/Databases/671-Mar24-12h',...
                    'src-ghost.db');

% Size map
sizeMapPath = fullfile(CITY_DATA_PATH, 'models/cam671/', 'mapSize.tiff');


%% Work

% Creating a simple DatabaseWriter instance
writer = DatabaseWriter(dbPath, refPath);

% Size map
mapSize = imread(sizeMapPath);

% Reading the image listing from the db
imagefiles = sqlite3.execute(writer.dbId, 'SELECT imagefile FROM images');
fprintf('found %d frames in the db.\n', length(imagefiles));

% Getting the boxes before for the camera (only if based on sizemap candidates)
cands = CandidatesSizemap (mapSize);
bboxes = cands.getCandidates();

% Selective Search candidates
%cands = CandidatesSelectSearch('mapSize', mapSize);
    
for i = 1:length(imagefiles)
    imagefile = imagefiles(i).imagefile;
    
    % Reading the ghost
    image = imread (fullfile(CITY_DATA_PATH, imagefile));
    
    % Getting the candidates (selective search)
    %bboxes = cands.getCandidates('image', image);

    % Get the mask
    query = 'SELECT maskfile FROM images WHERE imagefile = ?';
    maskfile = sqlite3.execute(writer.dbId, query, imagefile);
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
    writer.saveBoxesToDatabase(fildtersBboxes, imagefile, 'candidate');
    
    fprintf('%s: %d candidates\n', imagefile, size(fildtersBboxes,1));
end

% Closing the database / DatabaseWriter
writer.closeDatabase();
