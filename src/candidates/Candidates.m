classdef Candidates < CandidatesBase
    % Class to generate candidates for CNN's detection
    % Based on the geometry of the camera : pick the box based on the size
    % over the lanes
    
    properties
    end
    
    methods
        % Getting the candidate boxes
        function bboxes = getCandidates (self, varargin)
            bboxes = [];
        end
    end
        
end

