#!/bin/sh

matlab_exec=/Applications/MATLAB_R2014b.app/bin/matlab
cd /Users/evg/projects/City-Project/src/extra/videoDownload/

$matlab_exec -r "downloadSingleCam (578, '/Users/evg/projects/City-Project/data/camdata/cam578/Mar15-07h', 20); exit"
