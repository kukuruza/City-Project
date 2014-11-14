% Interface to MetricLearner to look up function signatures

classdef MetricLearnerInterface < handle
    methods (Abstract)
        
        % newCarNumber - a scalar, number of matched cars in the new frame
        % transitionMatrix = [newCars x seenCars]
        % newCarIndices - a vector, 0 == seenCar, 1 == newCar
        %
        %function [newCarNumber, transitionMatrix, newCarIndices] = 
        processFrame (ML, image, cars)

    end % methods
end