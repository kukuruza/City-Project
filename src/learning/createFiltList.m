% createFiltList - creates a list of good cars
%   It has to do with the way the cars are learned -- first all cars
%   are saved, than bad patches are deleted from 'patches' dir manually.
%   We need to complete filtering in other dirs.


clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../rootPathsSetup.m;
run ../subdirPathsSetup.m;


%% input

inDir = [CITY_DATA_PATH 'learning/cam572-sparse/'];
filtGoastsName = 'goasts1/';
origGoastsName = 'goasts0/';


%% output
goodListName = 'oneCarList.txt';
badListName = 'badList.txt';


%% work

goodFid = fopen ([inDir goodListName], 'w');
badFid = fopen ([inDir badListName], 'w');

origDirList = dir ([inDir origGoastsName]);
goodDirList = dir ([inDir filtGoastsName]);

j = 1;
ok = false;
while ~ok
    [~, goodName, ~] = fileparts(goodDirList(j).name);
    if ~isempty(goodName) && goodName(1) ~= '.', ok = true; end
    j = j + 1;
end

for i = 1 : length(origDirList)
    [~, origName, ~] = fileparts(origDirList(i).name);
    if isempty(origName) || origName(1) == '.', continue, end;
    
    if strcmp(origName, goodName)
        fprintf (goodFid, '%s\n', goodName);
        ok = false;
        while ~ok && j <= length(goodDirList)
            [~, goodName, ~] = fileparts(goodDirList(j).name);
            if ~isempty(goodName) && goodName(1) ~= '.', ok = true; end
            j = j + 1;
        end
    else
        fprintf (badFid, '%s\n', origName);
    end

end

fclose(goodFid);
fclose(badFid);

