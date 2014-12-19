function computeOrientationMap(obj)
    % Function to get the expected orientation of cars at a particular
    % point using geometry information
    %
    % Usage: 
    % geometryObject.computeOrientationMap();
    %
    % Function:
    % Computes and stores the orientation map in the internal variable that
    % can be accessed using the getter for the object
    
    % Compute the angle made using vanishing Pt and current Pt
    % (for only points on the road)
    roadMask = obj.roadMask > 0;
    
    
        
    obj.orientationMap = zeros(obj.imageSize);
end

