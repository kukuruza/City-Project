%
% Interface for choosing candidate boxes, e.g. selective search
%


classdef CandidatesInterface
    methods (Abstract)
        
        % bboxes = [x1 y1 width height] x N
        bboxes = getCandidates (self, varargin)
        
    end
end
