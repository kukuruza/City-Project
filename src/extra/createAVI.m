function createAVI (jpgInDir, aviOutPath)
%CREATEAVI (jpgInDir, aviOutPath)
%Convert jpg to avi
%
%@author: Lynna, Evgeny
%
%TODO: images from internet apparently have different time interval

outputVideo = VideoWriter (aviOutPath);
outputVideo.FrameRate = 1;
open(outputVideo);

imageNames = dir(fullfile(jpgInDir, '*.jpg'));
imageNames = {imageNames.name}';

imageStrings = regexp([imageNames{:}],'(\d*)','match');
imageNumbers = str2double(imageStrings);
[~,sortedIndices] = sort(imageNumbers);
sortedImageNames = imageNames(sortedIndices);

for ii = 1:length(sortedImageNames)
    img = imread(fullfile(jpgInDir, sortedImageNames{ii}));

    writeVideo(outputVideo,img);
end

close(outputVideo);
