% test that the background substraction class works the same way
%   as the original Lynna's code

clear all

workingDir = '/Users/evg/Box Sync/City Project/data/five camera for 2 min';
resultDir = fullfile(workingDir,'Result');
videoName = fullfile(resultDir,'shuttle_out.avi');


subtractor = BackgroundSubtractor ();


videoSource = vision.VideoFileReader(videoName,'ImageColorSpace','Intensity','VideoOutputDataType','uint8');
videoPlayer = vision.VideoPlayer();

while ~isDone(videoSource)
     frame  = step(videoSource);
     [mask, blobs, frame_out] = subtractor.subtract(frame);
     step(videoPlayer, mask);
end

release(videoPlayer);
release(videoSource);
