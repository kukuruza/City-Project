function computeOrientationMap(obj, initialPitchAngle)
    % Function to get the expected orientation of cars at a particular
    % point using geometry information, given an initialPitchAngle for the 
    % last row of the image (assumed 40 deg otherwise)
    %
    % Usage: 
    % geometryObject.computeOrientationMap();
    %
    % Function:
    % Computes and stores the orientation map in the internal variable that
    % can be accessed using the getter for the object
    % orientationMap has .yaw and .pitch as attributes
    
    if(nargin < 2)
        initialPitchAngle = 40; % 40 degrees
    end
    
    % Compute the angle made using vanishing Pt and current Pt
    % (for only points on the road)
    roadMask = obj.roadMask > 0;
    
    % Roll is zero as the car is always on the road
    % Vanishing plane parallel to the x axis
   
    [xId, yId] = meshgrid(1:obj.imageSize(2), 1:obj.imageSize(1));
    
    % Yaw is based on the x displacement wrt the vanishingPt x
    roadElems = find(roadMask == 1);
    yawMap = zeros(obj.imageSize);
    
    yawMap(roadElems) = atan(double(xId(roadElems) - obj.road.vanishPt(1)) ...
                    ./ (yId(roadElems) - obj.road.vanishPt(2)));
    
    % Pitch is based on a linear relationship (approximate) for 40 degrees
    pitchMap = initialPitchAngle * (yId - obj.road.vanishPt(2)) ...
                    / (obj.imageSize(1) - obj.road.vanishPt(2)) .* roadMask; 
    
   
    % (598, 254)
    obj.orientationMap.yaw = yawMap;
    obj.orientationMap.pitch = pitchMap;
end

