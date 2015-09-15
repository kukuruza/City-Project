classdef CandidatesBase < CandidatesInterface
    properties (SetAccess = public, GetAccess = public)
        % Threshold for checking for background occupancy to filter candidates
        occupancyThreshold
    end
    
    methods
        % Filter candidates by candidate
        filteredBoxes = filterCandidatesBackground(self, bboxes, background);
    end
    
    methods(Static)
        % Visualizing the candidates
        function debugImg = drawCandidates (bboxes, image)
            if(size(bboxes, 1) > 0)
                % get random colors
                cmap = colormap(lines(size(bboxes,1)));
                % init with random colors
                shapeInserter = vision.ShapeInserter( ...
                'BorderColor', 'Custom', 'CustomBorderColor', uint8(cmap * 255), ...
                                   'LineWidth', 2);

                % Draw in white 
    %             shapeInserter = vision.ShapeInserter( ...
    %             'BorderColor','Custom','CustomBorderColor', uint8([255 255 255]), ...
    %                                'LineWidth', 1);
                % draw
                debugImg = step(shapeInserter, image, uint32(bboxes));
            else
                % return the same image if no boxes are detected
                debugImg = image;
            end
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
        
        % Reading the output from CNN
        % Format <image no> <class> <probability>
        % Here <image no> is the sub image dumped => candidate
        % <class> is either 0 (no car) or 1 (car)
        % <probability> denotes the class confidence
        function debugImage = readPlotCNNResults(resultPath, image, bboxes)
            % Read the CNN result image
            fileId = fopen(resultPath);
            results = textscan(fileId, '%d %d %f\n');
            
            % Get the corresponding true boxes
            detections = bboxes(results{2} == 1, :);
            
            % Plot the boxes on the image
            debugImage = CandidatesBase.drawCandidates(detections, image);
        end
    end % methods(Static)
end