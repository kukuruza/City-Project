% interface for detector

classdef CarDetectorInterface < handle
    methods (Abstract)
        
        % method returns car objects
        cars = detect (CD, img)
        
    end % methods
end