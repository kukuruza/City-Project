function  Segment(ImName)
% SEGMENT  - Main graph cuts segmentation function
% SEGMENT(IMNAME) - ImName - Image to segment


% Global variables referenced in this function
global sopt SegImage fgpixels bgpixels;

% Segmented output placeholder
SegImage = zeros(size(ImName));

% GUI specific flag
fgflag = 2;

% Read the input image
I = imread(ImName);
I1 = I(:,:,1);
I2 = I(:,:,2);
I3 = I(:,:,3);

% Get Foreground and Background Pixels
% FY = fgpixels(:,1);
% FX = fgpixels(:,2);
% 
% BY = bgpixels(:,1);
% BX = bgpixels(:,2);

[h,w,~]=size(I);
[FY0,FX0]=meshgrid(floor(0.2*h):floor(0.8*h),floor(0.2*w):floor(0.8*w));
FY = reshape(FY0,[],1);
FX = reshape(FX0,[],1);
[BY0,BX0]=meshgrid([2:floor(0.2*h)-1,floor(0.8*h)+1:h],2:w);
BY1 = reshape(BY0,[],1);
BX1 = reshape(BX0,[],1);
[BY2,BX2]=meshgrid(floor(0.2*h):floor(0.8*h),[2:floor(0.2*w),floor(0.8*w):w]);
BY3 = reshape(BY0,[],1);
BX3 = reshape(BX0,[],1);
BY = [BY1;BY3];
BX = [BX1,BX3];

% Get Watershed pixels
L = watershed(I(:,:,1));

%%%%%%%%% Finding Mean colors of the regions  %%%%%%%%%%%%%%%%%%
numLabels = max(L(:));
PI = regionprops(L,'PixelIdxList');

MeanColors = zeros(numLabels,3);
for i=1:numLabels
    MeanColors(i,1) = mean(I1(PI(i).PixelIdxList));
    MeanColors(i,2) = mean(I2(PI(i).PixelIdxList));
    MeanColors(i,3) = mean(I3(PI(i).PixelIdxList));
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%% Finding Foreground and Background Labels from pixel seeds%%
try
    Findices = sub2ind(size(I1),FX,FY);
    FLabels = L(int32(Findices));
    FLabels = union(FLabels,[]);         %% Set-ifying the set of labels (Sorting)
    if(FLabels(1)==0)                   %% Removing Boundary Labels
        FLabels = FLabels(2:end);
    end

    Bindices = sub2ind(size(I1),BX,BY);
    BLabels = L(int32(Bindices));
    BLabels = union(BLabels,[]);         %% Set-ifying the set of labels
    if(BLabels(1)==0)                   %% Removing Boundary Labels
        BLabels = BLabels(2:end);
    end
catch
    beep
    disp('Error: Seeds are outside Image limits ..Please restart');
    return;
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Finding foregound and background color clusters %%%%%%%%%%%%

FColors = MeanColors(FLabels,:);
BColors = MeanColors(BLabels,:);

NumFClusters = sopt.NumFClusters_SS;
NumBClusters = sopt.NumBClusters_SS;

try
    [IDX, FCClusters] = kmeans(FColors, NumFClusters);  %% FCClusters = Foreground color clusters
    [IDX, BCClusters] = kmeans(BColors, NumBClusters);  %% BCClusters = Background color clusters
catch
    beep
    disp('Error!! Number of seeds should be greater than number of clusters ....');
    disp('Add more seeds or reduce number of clusters ...');
    return;
end

% Clustering is columnwise, clusters each set of fcolors into n clusters

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%  The Mex Function for GraphCutSegment %%%%%%%%%%%%
L = L-1;        %% Segments labeled from 0 now -- -1 is for boundary pixels
FLabels = FLabels-1;
BLabels = BLabels-1;
SegImage = GraphCutSegmentLazy(L, MeanColors, FLabels, BLabels, FCClusters, BCClusters);

%%%%%%%%%%%%%%%    Display the segmented image   %%%%%%%%%%%%%%%
SegImage = repmat(SegImage,[1,1,3]);
SegNewImage = uint8(SegImage) .* uint8(I);
figure;imshow(uint8(SegNewImage));

SegMask = SegImage;
SegResult = SegNewImage;

% Save Segmentation Result
save('SegResult', 'SegMask', 'SegResult');

