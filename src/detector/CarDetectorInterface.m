% interface for detector

classdef CarDetectorInterface < handle
    methods (Abstract)
        
        % method returns car objects
        detect (CD, image);
        
    end % methods
end