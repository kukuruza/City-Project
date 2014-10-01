% Metric learning method for identifying same cars
%


classdef MetricLearner < handle
    properties (Hidden)
        framecounter = 0;
        seenAppearCars = [];   % cars from previous frames
    end % properties
    methods
        function newCarNumber = processFrame (ML, image, foregroundMask, cars)
            ML.framecounter = ML.framecounter + 1;
            
            % cars - instances of Car class
            appearCars = [];
            for car = cars
                appearCars = [appearCars, AppearanceCar(car, ML.framecounter)];
            end
            
            % extract features
            for appCar = appearCars
                appCar.generateFeature (image, foregroundMask);
            end
            
            % construct similarity matrix with seen cars
            spatialConstraints = GeometryEstimator.mutualProb (appearCars, ML.seenAppearCars, 1);
            for i = 1 : length(appearCars)
                appCar = appearCars(i);
                for j = 1 : length(ML.seenAppearCars)
                    seenAppCar = ML.seenAppearCars(j);
                    % appearConstraints(i,j) = distance function (appCar.feature, seenAppCar.feature);
                end
            end
            % element-wise operation to come up with a single matrix
            constraints = spatialConstraints .* appearConstraints;
            
            % do matching
            %%% logic
            
            % return the new number
            %%% newCarNumber = 
            
            % == bookkeeping ==
            
            % prune the seen list and remove too old cars from there
            % for appearCar = ML.seenAppearCars find iFrame > ...
            
            % put the new cars into the list
            ML.seenAppearCars = [ML.seenAppearCars, appearCars];
        end
    end % methods
end