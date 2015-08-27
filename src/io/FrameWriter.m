% An interface for writing frames
%

classdef FrameWriter < handle
    methods (Abstract)
        
        % writeNextFrame combines frameImgs into a single image
        %   as specified by interface implementation,
        %   and writes that frame
        step (FW, images)
        
    end

end
