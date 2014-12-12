function computeCameraRoadMap(obj)
    % Creating map of expected car sizes at different locations on
    % the image - should also include the orientation extension
    % because of the orientations
    [~, mask] = meshgrid(1:obj.imageSize(2), 1:obj.imageSize(1));

    %Need to normalize the image co-ordinates using f 
    % Alternatively, we calibrate using the average lane width and
    % calculate the scale factor accordingly
    mask = max(double(mask - obj.road.vanishPt(2)) * obj.road.scaleFactor * obj.road.carHeightMu, zeros(obj.imageSize));

    % Ignoring points outside the roadMask
    mask = mask .* (obj.roadMask ~= 0);
    obj.cameraRoadMap = 2 * mask;
end