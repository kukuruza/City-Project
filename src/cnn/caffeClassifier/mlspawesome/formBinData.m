imSize = [54 54];

croppedDirName = 'test/cropped';
binFilePath = 'test/svhn_test.bin';

workStruct = digitStructCrop;

numData = length(workStruct);
modifiedX = zeros(numData, 3 * imSize(1) * imSize(2));
y = zeros(numData, 1);

%NumDigits = 4;

for i = 1:numData
    
    % form multi-digit number from digits
    digits = '00000';
    L = length(workStruct(i).bbox);
    digits(1) = num2str(L);
    for j = 1:L
        assert (L <= 4 && L > 0);
        % plus 1 because the 1st char is L
        digits(4-L+j + 1) = num2str(mod(workStruct(i).bbox(j).label, 10));
    end
    y(i) = str2num(digits);
    y(i) = int32(y(i));
    
    im = imread(fullfile(croppedDirName, [workStruct(i).name]));
    
    x = imresize(im, imSize);
    assert (ndims(x) == 3);

    a1 = x(:,:,1);
    a2 = x(:,:,2);
    a3 = x(:,:,3);
    final = [a1(:)' a2(:)' a3(:)'];
    modifiedX(i,:) = final;

end

finalResult = [y modifiedX];
s = strcat(binFilePath);
fileID = fopen(s,'w');
fwrite(fileID,finalResult');
fclose(fileID);
