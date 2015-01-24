% interface for detector

classdef CarDetectorBase < CarDetectorInterface
    properties
            % size distribution is considered gaussian
            sizeMean = 1.1;
            sizeSigma = 0.5;
    end
    methods (Hidden)
        
        function cars = filterCarsBySize (CD, cars, sizeMap, varargin)
            % validate input
            parser = inputParser;
            addRequired(parser, 'cars', @(x) isempty(x) || isa(x, 'Car'));
            addRequired(parser, 'sizeMap', @(x) ismatrix(x));
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, cars, sizeMap, varargin{:});
            parsed = parser.Results;
            
            maxSizeScore = normpdf(0,0,CD.sizeSigma);
            
            badindices = false(length(cars),1);
            for i = 1 : length(cars)
                center = cars(i).getBottomCenter(); % [y x]
                expectedSize = sizeMap(center(1), center(2));
                
                % assign score
                actualSize = sqrt(double(cars(i).bbox(3) * cars(i).bbox(4)));
                normSize = actualSize / double(expectedSize);
                cars(i).score = normpdf(normSize, CD.sizeMean, CD.sizeSigma) / maxSizeScore;

                % check if car is in forbidden area altogether
                if expectedSize == 0
                    if parsed.verbose > 1
                        fprintf ('    car %d - in forbidden sizeMap area\n', i); 
                    end
                    badindices(i) = true;
                else
                    if parsed.verbose > 2
                        fprintf ('    car %d - ok, score: %f\n', i, cars(i).score); 
                    end
                end
            end
            cars(badindices) = [];
        end
        
    end
end