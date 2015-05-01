classdef Candidates < CandidatesInterface
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
    
    methods(Static)
        % Visualizing the candidates
        function debugImg = drawCandidates (bboxes, image)
            debugImg = step(vision.ShapeInserter, image, uint32(bboxes));
        end
        
        % Save the candidate boxes
        function saveCandidates(bboxes, fileName)
            fileId = fopen(fileName, 'w');
            
            % Writing it to the file
            for i = 1:size(bboxes, 1)
                fprintf(fileId, '%d %d %d %d\n', ...
                    bboxes(i, 1), bboxes(i, 2), bboxes(i, 3), bboxes(i, 4));
            end
            
            fclose(fileId);
        end
        
        % Load the candidate boxes from the given file
        function bboxes = loadCandidates(fileName)
            if ~exist(fileName, 'file')
                warning('File name %s does not exist!\n', fileName);
                bboxes = [];
            else
                % Reading from the file
                fileId = fopen(fileName, 'r');
                bboxes = textscan(fileId, '%d %d %d %d\n');
                bboxes = cell2mat(bboxes);
            end
        end
    end
    
end

