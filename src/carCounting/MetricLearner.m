% Metric learning method for identifying same cars
%


classdef MetricLearner < handle
    properties (Hidden)
        framecounter = 0;
        seenCarapps = [];   % cars from previous frames
    end % properties
    methods
        function newCarNumber = processFrame (ML, image, foregroundMask, cars)
            
            % validation of parameters
            assert (ndims(image) == 3);         % color image
            assert (ismatrix(foregroundMask));  % grayscale mask
            assert (all([size(image,1) size(image,2)] == size(foregroundMask)));
            if ~isempty(cars), assert (isa(cars(1), 'Car')), end % cars are of class Car
            
            ML.framecounter = ML.framecounter + 1;
            
            % make CarAppearance objects from Car objects
            carapps = [];
            for car = cars
                carapp = CarAppearance (car, ML.framecounter);
                carapps = [carapps, carapp];
            end
            
            % extract features
            for carapp = carapps
                carapp.generateFeature (image, foregroundMask);
            end
            
            % construct similarity matrix with seen cars
            spatialConstraints = GeometryEstimator.mutualProb (carapps, ML.seenCarapps, 1);
            for i = 1 : length(carapps)
                carapp = carapps(i);
                for j = 1 : length(ML.seenCarapps)
                    seenCarapp = ML.seenCarapps(j);
                    % appearConstraints(i,j) = distance function (carapp.feature, seenCarapp.feature);
                end
            end
            % element-wise operation to come up with a single matrix
            constraints = spatialConstraints .* appearConstraints;
            
            % do matching
            % TODO: logic
            
            % return the new number
            % newCarNumber =  % TODO: logic
            
            % == bookkeeping ==
            
            % prune the seen list and remove too old cars from there
            % for appearCar = ML.seenAppearCars find iFrame > ...
            
            % put the new cars into the list
            ML.seenCarapps = [ML.seenCarapps, carapps];
        end
    end % methods
end