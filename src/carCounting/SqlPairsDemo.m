%
% example of reading cars db from matlab
%


clear all
% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));
% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


%% input

db_path = [CITY_DATA_PATH 'datasets/labelme/Databases/572/src-pairs.db'];



%% work

% open database
sqlite3.open (db_path);

% read imagefiles, each of them is a pair of images
pairfiles = sqlite3.execute('SELECT imagefile FROM images');

for i = 1 : length(pairfiles)
    % get the field 'imagefile' from i-th element of the structures
    pairfile = pairfiles(i).imagefile;
    
    % get (distinct) matches for this pairfile
    query = 'SELECT DISTINCT match FROM matches WHERE carid IN (SELECT id FROM cars WHERE imagefile = ?)';
    matches = sqlite3.execute(query, pairfile);
    
    fprintf ('%s: found %d matches.\n', pairfile, length(matches));
    
    for j = 1 : length(matches)
        % get the field 'match' from the j-th element of the structures
        match = matches(j).match;
        
        % get all info about two (or one if no match) cars for this match
        query = 'SELECT * FROM cars WHERE id IN (SELECT carid FROM matches WHERE match = ?)';
        car_entries = sqlite3.execute(query, match);
            
        % some database logic from Evgeny's side: not matched if carid == 0
        % get carids. It is 0 if no match
        carids = sqlite3.execute('SELECT carid FROM matches WHERE match = ?', match);
        if carids(1).carid == 0
            assert (length(car_entries) == 1);
            fprintf ('  match #%d: none - %d.\n', match, car_entries(1).id);
        elseif carids(2).carid == 0
            assert (length(car_entries) == 1);
            fprintf ('  match #%d: none - %d.\n', match, car_entries(1).id);
        else
            assert (length(car_entries) == 2);
            fprintf ('  match #%d: %d - %d.\n', match, car_entries(1).id, car_entries(2).id);
        end
    end
    
end

sqlite3.close();


