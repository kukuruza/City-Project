% Get the corresponding point using homography error
function[oppositePt] = getOppositePoint(obj, point, line, oppLine)
    % This method assumes the presence of two extreme for the road,
    % gets the opposite point on the other side of cannonical
    % road, for a given point. 
    % Uses homography and projects it back to get error for the
    % best fit
    %
    % Usage: 
    % oppositePt=geometryObject.getOppositePoint(point,line,oppLine);
    %

    % Collect points in pts1 and pts2 for homography computation
    % Vanishing points go to each other
    % Center of the frame at the current y of vanishPt
    pts1 = [obj.imageSize(2)/2; obj.road.vanishPt(2)]; 
    pts2 = obj.road.vanishPt;
    
    oppositePt = [];
end

%function getPointsa