% script analyzes color and JPEG produced noise at some part of video


clear all

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path
cd (fileparts(mfilename('fullpath')));        % change dir to this script



%% input

numframes = 100;
% roi = [109, 487, 137, 700];  % roi of the bright concrete fence
roi = [400, 410, 480, 547];  % roi of the front part of the road
thresh = 2.5e+7;

inVideoDir = [CITY_DATA_PATH 'camdata/cam572/5pm/'];
inVideoPath = [inVideoDir '15-mins.avi'];
inTimestampPath = [inVideoDir '15-mins.txt'];




%% work

frameReader = FrameReaderVideo (inVideoPath, inTimestampPath);

data = zeros(numframes, (roi(3)-roi(1)+1)*(roi(4)-roi(2)+1)*3);

% collect data
for t = 1 : numframes
    frame = frameReader.getNewFrame();
    if isempty(frame), break, end
    
    patch = frame(roi(1):roi(3), roi(2):roi(4), :);
    data(t,:) = patch(:)';
end

clear frameReader


% filter out outliers (when cars are around)
hists = zeros(numframes,256*3);
K = numel(patch)/3;
for t = 1 : numframes
    hists(t, 1:256) = histcounts(data(t,1:K), 0:256);
    hists(t, 256+1:256*2) = histcounts(data(t,K+1:K*2), 0:256);
    hists(t, 256*2+1:256*3) = histcounts(data(t,K*2+1:K*3), 0:256);
end
center = trimmean(hists, 0.1, 1);
corr = zeros (numframes,1);
for t = 1 : numframes
    corr(t) = sum(abs(hists(t,:) .* center));
end
for t = numframes : -1 : 1
    if corr(t) < thresh
        data(t,:) = [];
    end
end


% estimate color noise
noisehist = histcounts(std(data), 0:256);
plot(noisehist)


