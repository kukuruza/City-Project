imSize = [54 54];

scheme = 'train/';

croppedDirName = [scheme 'cropped-30'];
binFilePath = [scheme 'train_d1_54.bin'];

clear digitStructCrop
load ([scheme 'digitCrop.mat']);
workStruct = digitStructCrop;

patchDir = [scheme 'patches/'];

% only care about numbers of exactly that digits
NumDigits = 3;

% take only this digit
DigitPosition = 3;

% number of image warping
duplNum = 1;

    
numData = length(workStruct);

% count number of 3-digit numbers
counter = 0;
for i = 1:numData
    L = length(workStruct(i).bbox);
    if L == NumDigits, counter = counter + 1; end
end
exactDigitData = counter;

modifiedX = zeros(exactDigitData * duplNum, 3 * imSize(1) * imSize(2));
y = zeros(exactDigitData * duplNum, 1);

counter = 0;
for i = 1:numData
    if mod(i, 100) == 0, fprintf ('%d\n', i); end
    
    % skip the cycle if number of digits is not what we need
    L = length(workStruct(i).bbox);
    if L ~= NumDigits, continue; end
    
    counter = counter + 1;
    
    
    im = imread(fullfile(croppedDirName, [workStruct(i).name]));
    %imwrite(im, '~/Desktop/im2.png');
    
    %im = rgb2hsv(im);
    %im(:,:,3) = imadjust(im(:,:,3));
    %im = uint8(hsv2rgb(im) * 255);
    
    im = imresize(im, [70 70]);
    assert (ndims(im) == 3);  % make sure it's a color patch
    
    for d = 1 : duplNum
    
        y(counter + duplNum-1) = mod(workStruct(i).bbox( DigitPosition ).label, 10);
    
        %figure(1)
        %imshow(uint8(im))

        levelAngle = 20;
        levelShift = 0;
        angle = (rand-0.5) * levelAngle;
        shift = (rand(2,1)-0.5) * levelShift;
        im1 = imrotate(im, angle, 'crop');

        a = (size(im,1) - imSize(1)) / 2 + 1;
        b = (size(im,1) + imSize(1)) / 2;
        im1 = im1(a+shift(1):b+shift(1), a+shift(2):b+shift(2), :);
        %im1 = imresize(im1, imSize);

        %im = rgb2hsv(im);
        %im(:,:,3) = wiener2(im(:,:,3), [3 3]);
        %im = uint8(hsv2rgb(im) * 255);

        assert (size(im1,1) == imSize(1) && size(im1,2) == imSize(2));
        
        %figure(2)
        %imshow(uint8(im1))
        %pause
    
        imwrite (im1, [patchDir workStruct(i).name]);

        a1 = im1(:,:,1);
        a2 = im1(:,:,2);
        a3 = im1(:,:,3);
        final = [a1(:)' a2(:)' a3(:)'];
        modifiedX(counter + duplNum-1, :) = final;
        
    end
end



finalResult = [y modifiedX];
s = strcat(binFilePath);
fileID = fopen(s,'w');
%fwrite(fileID,finalResult');
fclose(fileID);
