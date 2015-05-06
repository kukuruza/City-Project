% This function adds all the required paths to Matlab pathdef
%   It should be called in the beginning of the pipeline.
%

if isempty (getenv('CITY_PATH'))
    error ('CITY_PATH environmental variable is not set.');
end

% add all sub-directories from src/
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));

fprintf('subdirPathsSetup note: have added the whole dir tree to pathdef. \n');
