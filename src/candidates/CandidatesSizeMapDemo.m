% Script to test the functioning of the Candidates class

% Set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

switch camId
    case 572
        % Reading the image and mask
        camId = 572;
        %image = imread(fullfile(CITY_DATA_PATH, 'models/cam572/cam572.png'));
        mapSize = imread(fullfile(CITY_DATA_PATH, 'models/cam572/mapSize.tiff'));
        videoPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.avi'];
        timesPath = [CITY_DATA_PATH 'camdata/cam572/5pm/15-mins.txt'];
        frameReader = FrameReaderVideo (videoPath, timesPath);
        
    case 671
        image = imread(fullfile(CITY_DATA_PATH, 'models/cam671/backimage-Mar24-12h.png'));
        mapSize = imread(fullfile(CITY_DATA_PATH, 'models/cam671/mapSize.tiff'));
        imagePath = fullfile(CITY_DATA_PATH, 'camdata/cam671/frames-4pm/');
        frameReader = FrameReaderImages(imagePath);
end

% Takes in the roadMap for a camera and generates the candidates
cands = CandidatesSizemap (mapSize);
bg = BackgroundGMM();

% Get the candidates for the camera
bboxes = cands.getCandidates();

% Loop through the video stream
noFrames = 30;
for i = 1:noFrames
    frame = frameReader.getNewFrame();
    background = bg.subtract(frame);
    
    % Get the candidates filtered by background
    filteredBoxes = cands.filterCandidatesBackground(bboxes, background);
    
    % Display the candidates
    debugImg = cands.drawCandidates(filteredBoxes, frame);
    figure(1); imshow(debugImg)
    pause()
end
return
    
% Dumping the candidate images to the file system
%savePath = fullfile(CITY_DATA_PATH, 'cnn/testingCam572');
%cands.dumpCandidateImages(image, bboxes, savePath);

% Displaying the output : Shuffle output produces only N shuffled outputs
shuffle = false;
% output by N
N = 50;
if(~shuffle)
    debugImg = cands.drawCandidates(bboxes, image);
    imshow(debugImg)
else
    % % Shuffle to output randomly
    bboxes = bboxes(randperm(size(bboxes,1)), :);

    for i = 0 : floor(size(bboxes,1) / N)
        subset = bboxes(i*N+1 : min(size(bboxes,1),(i+1)*N), :);
        if isempty(subset), break; end
        debugImg = cands.drawCandidates(subset, image);
        figure(3); imshow(debugImg)
        waitforbuttonpress();
    end
end