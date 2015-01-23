% This function adds all the required paths to Matlab pathdef
%   It should be called in the beginning of the pipeline.
%

% check if everything hasn't already been set up
global CITY_PATHS_SET;
if isempty(CITY_PATHS_SET)
    CITY_PATHS_SET = true;

    % check that rootPathsSetup.m has been executed
    if ~exist ('CITY_SRC_PATH', 'var')
        % if not, check if that script is the parent dir. If so, execute it
        if exist ('rootPathsSetup.m', 'file')
            run 'rootPathsSetup.m';
        else
            error ('CITY_SRC_PATH is not set. Execute rootPathSetup.m first');
        end
    end

    % add all sub-directories from src/
    addpath(genpath(CITY_SRC_PATH));

    fprintf('subdirPathsSetup note: have added the whole dir tree to pathdef. \n');

end
