% Script to test the functioning of the Candidates class

% Setting up the paths
run ../rootPathsSetup.m

% Takes in the roadMap for a camera and generates the candidates
cands = Candidates();

% Reading the image and mask
camId = 572;
image = imread(fullfile(CITY_DATA_PATH, 'models/cam572/cam572.png'));
mapSize = imread(fullfile(CITY_DATA_PATH, 'models/cam572/mapSize.tiff'));

% Example boxes
bboxes = uint32(400 * rand(100, 4) + 1);
%cands.saveCandidates(bboxes, 'savedBoxes.txt');
%readBoxes = cands.loadCandidates('savedBoxes.txt');
debugImg = cands.drawCandidates(bboxes(1:10, :), image);
figure(3); imshow(debugImg)