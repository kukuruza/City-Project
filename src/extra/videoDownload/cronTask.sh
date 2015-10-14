#!/bin/bash
. $HOME/.bash_profile

# 1st argument must be the path to the camera list, relative to CITY_DATA_PATH
CameraListPath=$1

# 2nd argument must be the number of minutes
NumMinutes=$2

matlab -nodisplay -r "cd(fullfile(getenv('CITY_PATH'), 'src')); subdirPathsSetup; downloadMultipleCams('"$CameraListPath"', "$NumMinutes"); exit"
