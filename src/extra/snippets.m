% file snippet for renaming necessary files from a dir

myDir = [inDir 'frames/'];
list = dir (myDir);
for i = 1 : length(list)
    [~, name, ext] = fileparts(list(i).name);
    if isempty(name) || name(1) == '.', continue, end;
    if name(4) == '-'
        name2 = ['f0' name(2:end)];
        movefile ([myDir name ext], [myDir name2 ext]);
    end
end


% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script
