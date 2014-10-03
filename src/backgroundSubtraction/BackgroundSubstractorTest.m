% test that the background substraction class works the same way
%   as the original Lynna's code

clear all

workingDir = '/Users/evg/Box Sync/City Project/data/five camera for 2 min';
resultDir = fullfile(workingDir,'Result');
videoName = fullfile(resultDir,'shuttle_out.avi');


subtractor = BackgroundSubtractor (5, 30, 50);


videoSource = vision.VideoFileReader(videoName,'ImageColorSpace','Intensity','VideoOutputDataType','uint8');
videoPlayer = vision.VideoPlayer();

while ~isDone(videoSource)
     frame  = step(videoSource);
     [mask, bboxes] = subtractor.subtract(frame);
     frame_out     = subtractor.drawboxes(frame, bboxes);
     step(videoPlayer, [uint8(mask)*255 frame_out]);
     pause(0.5)
end

release(videoPlayer);
release(videoSource);
