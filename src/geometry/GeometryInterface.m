% Interface for GeometryEstimator
%   Its goal is to 1) provide function definitions to users of the class
%   2) provide definitions of feature-request functions

classdef GeometryInterface
    methods (Abstract)
        
        % get map for sizes of cars on the road (0 for forbiden areas)
        getCameraRoadMap (obj, inputImg)
        
        % get probability for a car to move from A to B
        getMutualProb (obj, car1, car2, frameDiff)

    end % methods
end