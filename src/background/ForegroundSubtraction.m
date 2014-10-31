% Background substraction

% workingDir = '/Users/lgui/Box Sync/City Project/data/five camera for 2 min';
% resultDir = fullfile(workingDir,'Result');
% videoName = fullfile(resultDir,'shuttle_out.avi');

workingDir = '/Users/lgui/Dropbox/City-Project/data/2-min';
resultDir = fullfile(workingDir,'Result');
videoName = fullfile(resultDir,'camera572.avi');



videoSource = vision.VideoFileReader(videoName,'ImageColorSpace','Intensity','VideoOutputDataType','uint8');
detector = vision.ForegroundDetector(...
       'NumTrainingFrames', 5, ... % 5 because of short video
       'InitialVariance', 30*30); % initial standard deviation of 30
   
   blob = vision.BlobAnalysis(...
       'CentroidOutputPort', false, 'AreaOutputPort', false, ...
       'BoundingBoxOutputPort', true, ...
       'MinimumBlobAreaSource', 'Property', 'MinimumBlobArea', 50);
shapeInserter = vision.ShapeInserter('BorderColor','White');

videoPlayer = vision.VideoPlayer();
N=0;

while ~isDone(videoSource)
   
     frame  = step(videoSource);
     fgMask = step(detector, frame);
     bbox   = step(blob, fgMask);
     
     out    = step(shapeInserter, frame, bbox); % draw bounding boxes around cars
     
  %   
   tic
 %  mask_out = denoiseForegroundMask (fgMask, fn_level, fp_level);
    mask_out = maskProcess(fgMask);
     toc
     imname = sprintf('result%d.jpg',N);
     imwrite(mask_out,fullfile(resultDir,imname));
     step(videoPlayer, mask_out); % view results in the video player
     N=N+1;
end
release(videoPlayer);
release(videoSource);