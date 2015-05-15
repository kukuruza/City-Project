% Get the probability map of next transition given a point /
% position of the car and overlaying for visualization
function[probMap, overlaidImg] = generateProbMap(obj, carOrPoint, frameDiff, image)

    probMap = zeros(obj.imageSize(1), obj.imageSize(2));
    % Checking if its a point or a car
    if(isobject(carOrPoint))
        point = [carOrPoint.bbox(1) + carOrPoint.bbox(3)/2 ; carOrPoint.bbox(2) + carOrPoint.bbox(4)];
    else
        point = carOrPoint;
    end

    % Indices for which roadMap exists
    ptsOnRoad = find(obj.roadMask ~= 0);
    [r, c] = ind2sub(obj.imageSize, ptsOnRoad);
    
    for i = 1:length(ptsOnRoad)
        if(rem(i, 1000) == 0)
            fprintf('%d %d \n', i, length(ptsOnRoad));
        end
        probMap(ptsOnRoad(i)) = obj.getMutualProb(point, [c(i), r(i)], frameDiff);
    end
    
    %Debugging
    %fprintf('Number of arguments %d \n', nargin);
    if(nargin < 4)
        overlaidImg = zeros(obj.imageSize);
        return
    end
    %Overlaying the probability map over the image
    %Normalizing to [0, 1] to [0, 255];
    probMapNorm = probMap / max(probMap(:));
    rgbMap = label2rgb(gray2ind(probMapNorm, 255), jet(255));

    %Creating mask for overlaying and ignoring small valued
    %probabilities
    mask = (probMapNorm < 10^-5);
    mask = mask(:, :, [1 1 1]);

    %overlaidImg(mask) =  image(mask);
    %overlaidImg(~mask) = rgbMap(~mask);
    overlaidImg = uint8(mask) .* image + uint8(~mask) .* rgbMap;

    %Marking the origin point 
    markerInserter = vision.MarkerInserter('Size', 5, 'BorderColor','Custom','CustomBorderColor', uint8([0 0 255]));
    overlaidImg = step(markerInserter, overlaidImg, uint32(point));
end