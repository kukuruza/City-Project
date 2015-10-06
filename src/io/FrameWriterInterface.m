% An interface for writing frames
%

classdef FrameWriterInterface < handle
    methods (Abstract)
        
        % 'step' writes next frame
        step (FW, images)
        
    end

end
