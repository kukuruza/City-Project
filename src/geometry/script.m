clear all
GeometryEstimatorTest;
carPos = [50 177];

pts = [50 151 97 124 197 237 217 306; 177 135 176 187 167 126 203 161];
%index = [1 1 2 3 4 5 5];

%car = Car([149 125 164 134]);
%carPos = uint8([149 + 164/2; 125 + 134/2]);
index = 5;
frameDiff = 1;
carPos = [pts(1, index) pts(2, index)];

tic; 
[probMap, overLaid] = geom.generateProbMap(carPos, frameDiff, image); 

figure; imshow(overLaid)
return
Anorm = A / max(A(:));
rgb = label2rgb(gray2ind(Anorm, 255), jet(255));
mask = (A < 10^-8);
mask = mask(:, :, [1 1 1]);

overLaid =  uint8(mask) .* image + uint8(~mask) .* rgb;
markerInserter = vision.MarkerInserter('Size', 5, 'BorderColor','Custom','CustomBorderColor', uint8([0 0 255]));
markedImg = step(markerInserter, overLaid, uint8(carPos));


figure; imshow(markedImg)
return
figure; imshow(image + A(:, :, [1 1 1]))
toc