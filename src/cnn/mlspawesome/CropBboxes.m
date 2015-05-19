clear digitStruct;

srcDirName = 'test/';
load( [srcDirName 'digitTest.mat'] );
croppedDirName = [srcDirName 'cropped-30'];

expandPerc = 0.30;

for i = 1:length(digitStruct)
    im = imread(fullfile(srcDirName, [digitStruct(i).name]));
    
    xmin = size(im,2);
    xmax = 1;
    ymin = size(im,1);
    ymax = 1;
    
    for j = 1:length(digitStruct(i).bbox)
        [height, width] = size(im);
        y1 = max(digitStruct(i).bbox(j).top+1,1);
        y2 = min(digitStruct(i).bbox(j).top+digitStruct(i).bbox(j).height, height);
        x1 = max(digitStruct(i).bbox(j).left+1,1);
        x2 = min(digitStruct(i).bbox(j).left+digitStruct(i).bbox(j).width, width);
        if x1 < xmin, xmin = x1; end
        if x2 > xmax, xmax = x2; end
        if y1 < ymin, ymin = y1; end
        if y2 > ymax, ymax = y2; end
        
    end
    
    box = [xmin ymin xmax-xmin+1 ymax-ymin+1];
    box = expandBboxes(box, expandPerc, im);
    im = im(box(2):box(4)+box(2)-1, box(1):box(3)+box(1)-1, :);
    
    imwrite(im, fullfile(croppedDirName, digitStruct(i).name));
    
    %imshow(im);
    %pause;
end