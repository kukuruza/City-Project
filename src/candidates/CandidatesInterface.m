%
% Interface for choosing candidate boxes for selective search
%


classdef CandidatesInterface
    methods (Abstract)
        
        % bboxes = [x1 y1 width height] x N
        bboxes = getCandidates (C, vargin)
        
        setVerbosity (CD, verbose)
        
    end
end
