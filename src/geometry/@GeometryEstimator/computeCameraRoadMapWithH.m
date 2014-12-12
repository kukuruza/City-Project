% Computing the camera road map, using homography for cannonical state
function computeCameraRoadMapWithH(obj)
    % Creating map of expected car sizes at different locations on
    % the image - should also include the orientation extension
    % because of the orientations
    [x, y] = meshgrid(1:obj.imageSize(2), 1:obj.imageSize(1));

    % Brute force looping for now
    % Compute the y co-ordinate in the warped image
    roadElems = find(obj.roadMask ~= 0);
    H = obj.homography;

    yWarped = zeros(obj.imageSize);
    yWarped(roadElems) = ...
       (H(2, 1)*x(roadElems) + H(2,2)*y(roadElems) +H(2,3)) ./ ...
       (H(3, 1)*x(roadElems) + H(3,2)*y(roadElems) +H(3,3) + eps);

    mask = max((yWarped-obj.road.vanishPt(2)) * ...
          obj.road.scaleFactor * obj.road.carHeightMu, zeros(obj.imageSize));

    % Assigning the road map calculated to the object
    obj.cameraRoadMap = 2 * mask;
end
