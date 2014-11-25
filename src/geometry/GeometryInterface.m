% Interface for GeometryEstimator
%   Its goal is to 1) provide function definitions to users of the class
%   2) provide definitions of feature-request functions

classdef GeometryInterface < handle
    methods (Abstract)
        
        % get map for sizes of cars on the road (0 for forbiden areas)
        sizeMap = getCameraRoadMap (obj)
        
        % get map of cars orientations on the road
        % TODO: output to be deterrmined
        orientationMap = getOrientationMap (obj)
        
        % get probability for a car to move from A to B
        prob = getMutualProb (obj, car1, car2, frameDiff)

        % generate the entire probability matrix between sets of cars from two frames
        probMatrix = generateProbMatrix (obj, carsFrame1, carsFrame2);
        
        % Interface to update the speed of the lanes based on approximate matching matrix
        %
        % carsFrame1 and carsFrame2 will be used to get an approach idea of
        % mean speed that is observed
        %
        % MatchingMat gives the confidence with which a speed estimated
        % from pair of cars is likely to be close to mean value
        %
        % GeometryMatrix helps to consider only viable cars according to
        % simple geometry rules (geoProb > 0 => Valid speed estimate
        updateSpeed(obj, carsFrame1, carsFrame2, matchingMat, geometryMatrix)
    end % methods
end