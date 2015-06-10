%
% Interface for choosing candidate boxes, e.g. selective search
%

classdef CandidatesInterface
    methods (Abstract)
        % bboxes = [x1 y1 width height] x N
        % Each row for a bounding box
        % Generating the candidates
        bboxes = getCandidates (self, varargin)
        
        % Visualizing the candidates
        debugImg = drawCandidates (bboxes, image);
        
        % Save the candidate boxes
        saveCandidates(bboxes, fileName);
        
        % Load the candidate boxes from the given file
        bboxes = loadCandidates(fileName);
        
        % Dumping the candidate sub-images into the folder
        dumpCandidateImages(images, bboxes, savePath);
    end
end
