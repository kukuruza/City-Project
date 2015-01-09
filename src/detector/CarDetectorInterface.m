% interface for detector

classdef CarDetectorInterface < handle
    methods (Abstract)
        
        % returns mask of where the cars are detected
        mask = getMask (CD)
        
        % method returns car objects
        cars = detect (CD, img)
        
    end % methods
end