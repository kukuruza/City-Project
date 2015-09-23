% interface for detector

classdef CarDetectorInterface < handle
    methods (Abstract)
        
        % method returns car objects
        cars = detect (CD, img)
        
        % set verbosity in every detector within
        setVerbosity (CD, verbose)
        
    end % methods
end