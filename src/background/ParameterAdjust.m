% Choose parameters


clear all

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% add all scripts to matlab pathdef
run ../subdirPathsSetup.m



%% input and ground truth
imagesDir = [CITY_DATA_PATH 'camdata/cam572/2-hours/'];
outImagePath = [CITY_DATA_PATH 'testdata/background/result/'];
groundtruthImagePath= [CITY_DATA_PATH 'testdata/background/groundtruth/'];

%% test




% background subtraction
background.num_training_frames = 5;
background.initial_variance = 30;

% mask refinement
%for i = 11%:20
%    for j = 2
i = 15;
j = 2;
background.fn_level = i;%15;
background.fp_level = j;%1;

% extracting bounding boxes
background.minimum_blob_area = 50;
         
N=0;
recall = [];
precision = [];
frameReader = FrameReaderImages (imagesDir);
background = Background();
while true
    frame = frameReader.getNewFrame();
    %[mask, bboxes] = subtractor.subtract(frame);
    [mask, bboxes] = background.subtractAndDenoise (frame);
    %bboxes
    frame_out = background.drawboxes(frame, bboxes);
 %   subplot(1,2,1),imshow(frame_out);
 %   subplot(1,2,2),imshow(mask);
    if mod(N,10)==0 & N~=0
        imname = fullfile(groundtruthImagePath,sprintf('mask%d.png',N));
        temp=logical(importdata(imname));
        groundtruth = temp(:,:,1);
        gm = groundtruth & mask;
        recall(N/10) = sum(gm(:))/sum(groundtruth(:));
        precision(N/10)=sum(gm(:))/sum(mask(:));
      %  groundtruth = imread(imname);
   %     recall(N/10)=
    %    imwrite(mask,fullfile(outImagePath,imname));
    end
    if N>200
        break
    end
 %   pause(0.5);
    N=N+1;
end
R(i-10,j) = mean(recall)
P(i-10,j) = mean(precision)
 %   end
%end
