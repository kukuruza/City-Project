#!/bin/bash
. $HOME/.bash_profile
. $HOME/.profile

# 1st argument must be the path to the camera list, relative to CITY_DATA_PATH
CameraListPath=$1

# 2nd argument must be the number of minutes
NumMinutes=$2

# 3rd argument is optional. If "true" the script will delete all files after downloaded is complete
if [ $# -eq 3 ]; then
    echo "deleteOnExit argument was provided, will take it value"
    DeleteOnExit=$3
else
    # default. Leave the downloaded files alone.
    DeleteOnExit="false"
fi


matlab -nodisplay -r "cd(fullfile(getenv('CITY_PATH'), 'src')); subdirPathsSetup; downloadMultipleCams('"$CameraListPath"', "$NumMinutes", 'deleteOnExit', "$DeleteOnExit"); exit"
