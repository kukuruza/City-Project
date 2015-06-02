classdef CandidatesBase < CandidatesInterface
    methods(Static)
        % Visualizing the candidates
        function debugImg = drawCandidates (bboxes, image)
            % get random colors
            cmap = colormap(lines(size(bboxes,1)));
            % init with random colors
            shapeInserter = vision.ShapeInserter( ...
            'BorderColor','Custom','CustomBorderColor', uint8(cmap * 255), ...
                               'LineWidth', 2);
            
            % Draw in white 
            %shapeInserter = vision.ShapeInserter( ...
            %'BorderColor','Custom','CustomBorderColor', uint8([255 255 255]), ...
            %                    'LineWidth', 1);
            % draw
            debugImg = step(shapeInserter, image, uint32(bboxes));
        end
        
        % Save the candidate boxes
        function saveCandidates(bboxes, fileName)
            fileId = fopen(fileName, 'w');
            
            % Writing it to the file
            for i = 1:size(bboxes, 1)
                fprintf(fileId, '%d %d %d %d\n', ...
                    bboxes(i, 1), bboxes(i, 2), bboxes(i, 3), bboxes(i, 4));
            end
            
            % Close the file
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
                
                % Close the file
                fclose(fileId);
            end
        end
    end % methods(Static)
end