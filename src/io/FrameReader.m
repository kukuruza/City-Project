% An interface for reading frames from any source

classdef FrameReader < handle
    methods (Abstract)
        
        % getNewFrame returns a new frame if there is any
        %   or [] in case of EOF or any errors
        getNewFrame(FR)
        
    end

end