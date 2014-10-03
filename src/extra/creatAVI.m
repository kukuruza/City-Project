% Convert jpg to avi

workingDir = '/Users/lgui/Box Sync/City Project/data/five camera for 2 min';
outputVideo = VideoWriter(fullfile(workingDir,'shuttle_out.avi'));
outputVideo.FrameRate = 1;%shuttleVideo.FrameRate;
open(outputVideo);

imageNames = dir(fullfile(workingDir,'cameraNumber360','*.jpg'));
imageNames = {imageNames.name}';

imageStrings = regexp([imageNames{:}],'(\d*)','match');
imageNumbers = str2double(imageStrings);
[~,sortedIndices] = sort(imageNumbers);
sortedImageNames = imageNames(sortedIndices);

for ii = 1:length(sortedImageNames)
    img = imread(fullfile(workingDir,'cameraNumber360',sortedImageNames{ii}));

    writeVideo(outputVideo,img);
end

close(outputVideo);

shuttleAvi = VideoReader(fullfile(workingDir,'shuttle_out.avi'));