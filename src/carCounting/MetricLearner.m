% Metric learning method for identifying same cars

classdef MetricLearner < MetricLearnerInterface
    properties (Hidden)
        % framecounter = 1;
        geometryObj;     
        seenCars = {};   % cars from previous frames
    end % properties
    properties
        WeightGeom = 0.4;    % can be changed outside
        WeightHog = 0.3;
        WeightCol = 0.3;
        Th = 0.5;
        framecounter = 1;
    end
    
    methods
        function ML = MetricLearner(geometryObj)
            ML.geometryObj = geometryObj;
        end
        
        
        function [ProbCol, ProbHOG] = AppProb (ML, CarObj1, CarObj2)   % don't need the ML to be the first argument, for this function doesn't change anything of ML
            % HOG
            
            dHOG = chi_square_statistics(CarObj1.histHog, CarObj2.histHog);
            ProbHOG = 1-dHOG;
            
            % Color          

            dCol = chi_square_statistics(CarObj1.histCol,CarObj2.histCol);
            ProbCol = 1-4*dCol;
        end
            
            
        function [newCarNumber, Match, NewIndex] = processFrame (ML, image, cars)  % delete the iframe input argument
            if (ML.framecounter == 1)
                newCarNumber = 0;
                for car = cars  % for all the car patches in cars
                    car.getROI ();
                    car.extractPatch(image);
                    car.generateFeature(image);
                end
                ML.seenCars{1} = cars;
                ML.framecounter = 2;
                Match = [];
                NewIndex = ones(length(cars), 1);
                return
            end
            
            % gewnerate appearance features
            for car = cars  % for all the car patches in cars
                car.getROI ();
                car.extractPatch(image);
                car.generateFeature(image);
            end
                
            % validation of arguments
            % color image
            assert (ndims(image) == 3 && size(image,3) == 3);
            % usual vector instead of cell array
            if ~isempty(cars), assert (~iscell(cars) && isvector(cars)); end
            % car is an object of class Car
            if ~isempty(cars), assert (isa(cars(1), 'Car')); end
                    
            % ML.framecounter = ML.framecounter + 1;
            seen = ML.seenCars{ML.framecounter-1};
            
            % compute matching probability between each in the new frame and each car in the former frames; construct similarity matrix with seen cars
          
            ProbCol = zeros(length(cars), length(seen));
            ProbHOG = zeros(length(cars), length(seen));
            ProbWeighted = zeros(length(cars), length(seen));
                     
            % probability of geometry
            ProbGeo = ML.geometryObj.generateProbMatrix(seen, cars);
            
            for i = 1 : length(cars)
                car = cars(i);      % all the cars in new frame
                for j = 1 : length(seen)
                    seenCar = seen(j);   % all the cars in former frame                
                    if(ProbGeo(i,j) == 0)
                        ProbCol(i,j) = 0;
                        ProbHOG(i,j) = 0;
                    else
                        [ProbCol(i,j), ProbHOG(i,j)] = ML.AppProb(car, seenCar);
                    end
                end
            end

            ProbWeighted = ML.WeightGeom * 100 * ProbGeo + ML.WeightCol * ProbCol + ML.WeightHog * ProbHOG;
            
            % Using the probability matrix and geometry matrix; updating
            % the speed of the model for better posterior estimate
            if(length(seen) > 0 && length(cars) > 0)
                ML.geometryObj.updateSpeed(seen, cars, ProbWeighted, ProbGeo);
            end
            
            % build the match matrix
            Match = zeros(size(ProbWeighted));
            NewIndex = zeros(length(cars), 1);
            for k = 1: length(cars)
                [maxProb, index] = max(ProbWeighted(k,:));
                if(maxProb> ML.Th)
                    Match(k,index) = 1;
                    NewIndex(k)= 0;
                else
                    NewIndex(k)= 1;
                end
            end
            % compute new car number
            CountMatch = sum(sum(Match));
            newCarNumber = length(cars) - CountMatch;
            ML.seenCars{ML.framecounter} = cars;
            
%             fileGeoProb = strcat('GeoProb', num2str(ML.framecounter));
%             save(fileGeoProb, 'ProbGeo');
%             fileGeoProb = strcat('ColProb', num2str(ML.framecounter));
%             save(fileGeoProb, 'ProbCol');
%             fileGeoProb = strcat('HOGProb', num2str(ML.framecounter));
%             save(fileGeoProb, 'ProbHOG');
            

            % element-wise operation to come up with a single matrix
            % constraints = GeoProb .* appearConstraints;

            ML.framecounter = ML.framecounter + 1;
            

            % == bookkeeping ==
            
            % prune the seen list and remove too old cars from there
            % for appearCar = ML.seenAppearCars find iFrame > ...

        end
    end % methods
end