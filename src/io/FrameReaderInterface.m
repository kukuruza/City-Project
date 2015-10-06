% An interface for reading frames from any source

classdef FrameReaderInterface < handle
    methods (Abstract)
        
        % getNewFrame returns a new frame if there is any
        %   or [] in case of EOF or any errors
        [frame, timestamp] = getNewFrame(self)
        
    end

end