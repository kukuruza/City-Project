% Function to return the 3D distance for the given geometry
function dist3D = computeDistance3D(obj, point1, point2)
    % Check for lower y-coordinate point
    yRatio = double(point1(2) - obj.road.vanishPt(2)) / (point2(2) - obj.road.vanishPt(2));

    % Check for points to be on the road
    assert(point1(2) > obj.road.vanishPt(2) || point2(2) > obj.road.vanishPt(2));

    % Flip the points if yRatio is less than 1
    if(yRatio < 1)
       yRatio = 1.0/yRatio;
    end

    % We care only about the distance along the road (for now)
    dist3D = 1/obj.road.scaleFactor * log(yRatio);

    % Debugging
    %if(~isreal(dist3D))
    %    fprintf('Distance, yRatio: %f %f \n', dist3D, yRatio);
    %end
end
