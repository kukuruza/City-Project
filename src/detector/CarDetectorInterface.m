% interface for detector

classdef CarDetectorInterface < handle
    properties
            sizeLimits = [0.7 1.5];
    end
    methods
        
        function cars = filterCarsBySize (CD, cars, sizeMap, varargin)
            % validate input
            parser = inputParser;
            addRequired(parser, 'cars', @(x) isempty(x) || isa(x, 'Car'));
            addRequired(parser, 'sizeMap', @(x) ismatrix(x));
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, cars, sizeMap, varargin{:});
            parsed = parser.Results;
            
            badindices = false(length(cars),1);
            for i = 1 : length(cars)
                center = cars(i).getBottomCenter(); % [y x]
                expectedSize = sizeMap(center(1), center(2));
                actualSize = sqrt(single(cars(i).bbox(3) * cars(i).bbox(4)));
                if actualSize < expectedSize * CD.sizeLimits(1) || ...
                   actualSize > expectedSize * CD.sizeLimits(2)
                    if parsed.verbose > 1
                        fprintf ('    car %d - bad size %f, expect %f\n', i, actualSize, expectedSize); 
                    end
                    badindices(i) = true;
                end
            end
            cars(badindices) = [];
        end
        
    end
    methods (Abstract)
        
        % returns mask of where the cars are detected
        mask = getMask (CD)
        
        % method returns car objects
        cars = detect (CD, img)
        
    end % methods
end