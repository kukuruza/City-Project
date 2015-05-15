h5nameTrain = 'black-white-orig-train.h5';
delete (h5nameTrain)
h5nameTest = 'black-white-orig-test.h5';
delete (h5nameTest)
clear Data szData

assert (~isempty(getenv('CITY_DATA_PATH')));
postmpl = fullfile(getenv('CITY_DATA_PATH'), 'clustering/color-572-Oct28-10h/white-gray-40x30/*.png');
negtmpl = fullfile(getenv('CITY_DATA_PATH'), 'clustering/color-572-Oct28-10h/black-40x30/*.png');

poslist = dir(postmpl);
neglist = dir(negtmpl);

N = length(poslist) + length(neglist);

for i = 1 : length(poslist)
    imgpath = fullfile(fileparts(postmpl), poslist(i).name);
    img = imread(imgpath);
    img = permute(img, [2 1 3]);

    if ~exist('szData', 'var')
        szData = [size(img) N]
        Data = double(zeros(szData));
    end
    
    Data(:,:,:,i) = img;
end
for i = 1 : length(neglist)
    imgpath = fullfile(fileparts(negtmpl), neglist(i).name);
    img = imread(imgpath);
    img = permute(img, [2 1 3]);

    Data(:,:,:,i+length(poslist)) = img;
end

% normalize
%Data = (Data - 128) / 128;

Labels = double (ones(1, N));
Labels (1:length(poslist)) = 0;

% shuffle
indices = randperm(N);
Data = Data (:,:,:,indices);
Labels = Labels (:,indices);

% split into train/test
percTrain = 0.7;
numTrain = floor(N * percTrain);
numTest = N-numTrain;
DataTrain = Data (:,:,:,1:numTrain);
LabelsTrain = Labels (:,1:numTrain);
DataTest = Data (:,:,:,numTrain+1:N);
LabelsTest = Labels (:,numTrain+1:N);

error('r')

h5create (h5nameTrain, '/data', [size(img) numTrain]);
h5write  (h5nameTrain, '/data', DataTrain);

h5create (h5nameTrain, '/label', [1 numTrain]);
h5write  (h5nameTrain, '/label', LabelsTrain);

h5create (h5nameTest, '/data', [size(img) numTest]);
h5write  (h5nameTest, '/data', DataTest);

h5create (h5nameTest, '/label', [1 numTest]);
h5write  (h5nameTest, '/label', LabelsTest);
