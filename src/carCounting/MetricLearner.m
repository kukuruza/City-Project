% Metric learning method for identifying same cars

classdef MetricLearner < handle
    properties (Hidden)
        framecounter = 0;
        seenCars = {};   % cars from previous frames
    end % properties
    methods
        function ML = MetricLearner()
            
            ML.framecounter = 0;
            ML.seenCars  = {};
            % a = 1
        
        end
        
        
        function [ProbCol, ProbHOG] = AppProb (ML, CarObj1, CarObj2)
            % HOG
            
            dHOG = chi_square_statistics(CarObj1.histHog,CarObj2.histHog);
            ProbHOG = 1-dHOG;
            
            % Color          

            dCol = chi_square_statistics(CarObj1.histCol,CarObj2.histCol);
            ProbCol = 1-4*dCol;
        end
            
            
        function [newCarNumber, Match, NewIndex] = processFrame (ML, iframe, image, cars, geometryObj)
            if (iframe == 1)
                newCarNumber = 0;
                ML.seenCars{iframe} = cars;
                ML.framecounter = 1;
                Match = 1;
                return
            end
                
            % validation of arguments
            % color image
            assert (ndims(image) == 3 && size(image,3) == 3);
            % usual vector instead of cell array
            if ~isempty(cars), assert (~iscell(cars) && isvector(cars)); end
            % car is an object of class Car
            if ~isempty(cars), assert (isa(cars(1), 'Car')); end
                    
            ML.framecounter = ML.framecounter + 1;
            seen = ML.seenCars{iframe-1};
            
            % compute matching probability between each in the new frame and each car in the former frames; construct similarity matrix with seen cars
          
            ProbCol = zeros(length(cars), length(seen));
            ProbHOG = zeros(length(cars), length(seen));
            ProbWeighted = zeros(length(cars), length(seen));
                     
            % probability of geometry
            ProbGeo = geometryObj.getProbMatrix(seen, cars, 1);

            for i = 1 : length(cars)
                car = cars(i);      % all the cars in new frame
                for j = 1 : length(seen)
                    seenCar = seen(j);   % all the cars in former frame                
                    %ProbGeo = geometryObj.getMutualProb(seen, cars, 1);  % seen car should be the first arguement
                    %fprintf('Prob : %f\n', ProbGeo(i,j));
                    [ProbCol(i,j), ProbHOG(i,j)] = ML.AppProb(car, seenCar);
                    ProbWeighted(i,j) = 0.5*100*ProbGeo(i,j) + 0.3*ProbCol(i,j) + 0.2*ProbHOG(i,j);
                end
            end
           
            % build the match matrix
            Match = zeros(size(ProbWeighted));
            NewIndex = zeros(length(cars), 1);
            for k = 1: length(cars)
                [maxProb, index] = max(ProbWeighted(k,:));
                if(maxProb>0.8)
                    Match(k,index) = 1;
                    NewIndex(k)= 1;
                else
                    NewIndex(k)= 0;
                end
            end
            % compute new car number
            CountMatch = sum(sum(Match));
            newCarNumber = length(cars) - CountMatch;    
            ML.seenCars{iframe} = cars;
            
%             fileGeoProb = strcat('GeoProb', num2str(iframe));
%             save(fileGeoProb, 'ProbGeo');
%             fileGeoProb = strcat('ColProb', num2str(iframe));
%             save(fileGeoProb, 'ProbCol');
%             fileGeoProb = strcat('HOGProb', num2str(iframe));
%             save(fileGeoProb, 'ProbHOG');
            

            % element-wise operation to come up with a single matrix
            % constraints = GeoProb .* appearConstraints;
            

            % == bookkeeping ==
            
            % prune the seen list and remove too old cars from there
            % for appearCar = ML.seenAppearCars find iFrame > ...

        end
    end % methods
end