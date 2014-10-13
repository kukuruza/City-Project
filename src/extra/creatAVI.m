% Convert jpg to avi
%
% @author: Lynna
%

clear all

camName = 'camera671';

run ../rootPathsSetup.m;

workingDir = [CITY_DATA_PATH '2-min/'];
outputVideoPath = fullfile (workingDir, [camName '.avi']);
outputVideo = VideoWriter (outputVideoPath);
outputVideo.FrameRate = 1;
open(outputVideo);

imageNames = dir(fullfile(workingDir, camName, '*.jpg'));
imageNames = {imageNames.name}';

imageStrings = regexp([imageNames{:}],'(\d*)','match');
imageNumbers = str2double(imageStrings);
[~,sortedIndices] = sort(imageNumbers);
sortedImageNames = imageNames(sortedIndices);

for ii = 1:length(sortedImageNames)
    img = imread(fullfile(workingDir, camName, sortedImageNames{ii}));

    writeVideo(outputVideo,img);
end

close(outputVideo);

shuttleAvi = VideoReader(fullfile(workingDir, [camName '.avi']));
