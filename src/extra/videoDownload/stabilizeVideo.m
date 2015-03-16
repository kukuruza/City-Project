clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;

videoName = [CITY_DATA_PATH 'camdata/cam578/Mar12-12h-sunny'];
videoPath = [videoName '.avi'];
timePath = [videoName '.txt'];
frameReader = FrameReaderVideo (videoPath, timePath);
[frame, ~] = frameReader.getNewFrame();


optical = vision.OpticalFlow( ...
    'OutputValue', 'Horizontal and vertical components in complex form');
% Initialize the vector field lines.

maxWidth = size(frame,2);
maxHeight = size(frame,1);
shapes = vision.ShapeInserter;
shapes.Shape = 'Lines';
shapes.BorderColor = 'white';
r = 1:5:maxHeight;
c = 1:5:maxWidth;
[Y, X] = meshgrid(c,r);
% Create VideoPlayer System objects to display the videos.

hVideoIn = vision.VideoPlayer;
hVideoIn.Name  = 'Original Video';
hVideoOut = vision.VideoPlayer;
hVideoOut.Name  = 'Motion Detected Video';
% Stream Acquisition and Processing Loop

% Create a processing loop to perform motion detection in the input video. This loop uses the System objects you instantiated above.

% Set up for stream
nFrames = 0;
while (nFrames<100)     % Process for the first 100 frames.
    % Acquire single frame from imaging device.
    [rgbData, ~] = frameReader.getNewFrame();
    rgbData = double(rgbData);

    % Compute the optical flow for that particular frame.
    optFlow = step(optical,rgb2gray(rgbData));

    % Downsample optical flow field.
    optFlow_DS = optFlow(r, c);
    H = imag(optFlow_DS)*50;
    V = real(optFlow_DS)*50;

    % Draw lines on top of image
    lines = [Y(:)'; X(:)'; Y(:)'+V(:)'; X(:)'+H(:)'];
    rgb_Out = step(shapes, rgbData,  lines');

    % Send image data to video player
    % Display original video.
    step(hVideoIn, uint8(rgbData));
    % Display video along with motion vectors.
    step(hVideoOut, uint8(rgb_Out));

    % Increment frame count
    nFrames = nFrames + 1;
end


release(hVideoIn);
release(hVideoOut);

