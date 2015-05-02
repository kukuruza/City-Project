% Script to test the functioning of the Candidates class

% Setting up the paths
run ../rootPathsSetup.m
run ../subdirPathsSetup.m

% Reading the image and mask
camId = 572;
image = imread(fullfile(CITY_DATA_PATH, 'models/cam572/cam572.png'));
mapSize = imread(fullfile(CITY_DATA_PATH, 'models/cam572/mapSize.tiff'));

% Takes in the roadMap for a camera and generates the candidates
cands = Candidates();

% Selective Search wrapper
%cands = CandidatesSelectSearch('mapSize', mapSize);
%bboxes = cands.getCandidates('image', image);

% Example boxes
%bboxes = uint32(400 * rand(100, 4) + 1);
%cands.saveCandidates(bboxes, 'savedBoxes.txt');
%readBoxes = cands.loadCandidates('savedBoxes.txt');

% shuffle to output randomly
bboxes = bboxes(randperm(size(bboxes,1)), :);
% output by N
N = 50;
for i = 0 : floor(size(bboxes,1) / N)
    subset = bboxes(i*N+1 : min(size(bboxes,1),(i+1)*N), :);
    if isempty(subset), break; end
    debugImg = cands.drawCandidates(subset, image);
    figure(3); imshow(debugImg)
    waitforbuttonpress();
end
