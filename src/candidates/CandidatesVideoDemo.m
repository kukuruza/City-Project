% Script to test the functioning of the Candidates class

% Set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script

% Reading the image and mask
%camId = 572;
image = imread(fullfile(CITY_DATA_PATH, 'models/cam572/cam572.png'));

% Video
videoPath = fullfile(CITY_DATA_PATH, 'camdata/cam572/5pm/15-mins.avi');
reader = FrameReaderVideo(videoPath, []);

mapSize = imread(fullfile(CITY_DATA_PATH, 'models/cam572/mapSize.tiff'));
%camId = 671;
% image = imread(fullfile(CITY_DATA_PATH, 'models/cam671/backimage-Mar24-12h.png'));
% mapSize = imread(fullfile(CITY_DATA_PATH, 'models/cam671/mapSize.tiff'));

% Loop
savePath = fullfile(CITY_DATA_PATH, 'cnn/testingCam572/%d/');

noFrames = 10;
for i = 1:10
    image = reader.getNewFrame();
    % Takes in the roadMap for a camera and generates the candidates
    cands = CandidatesSizemap (mapSize);

    % Selective Search wrapper
    %cands = CandidatesSelectSearch('mapSize', mapSize);

    tic
        bboxes = cands.getCandidates();
    %     bboxes = cands.getCandidates('image', image);
    toc

    % Dumping the candidate images to the file system
    
    cands.dumpCandidateImages(image, bboxes, ...
                            sprintf(savePath, i));
end

return
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