function filteredBoxes = filterCandidatesBackground(self, bboxes, background)
    % Filtering the candidates based on the background occupancy
    
    % Flag to keep the box
    keepBox = false(size(bboxes, 1), 1);
    bground = double(background);
    
    for i = 1:size(bboxes, 1)
        % Getting the occupancy in each of the box
        occupancy = bground(bboxes(i, 2) + (0:bboxes(i, 4)-1), ...
                                bboxes(i, 1) + (0:bboxes(i, 3)-1));
        occupancy = nnz(occupancy) / double(bboxes(i, 3) * bboxes(i, 4));
        
        % Threshold on the occupancy
        if(occupancy > self.occupancyThreshold)
            keepBox(i) = true;
        end
    end
    
    % Filtering the boxes
    filteredBoxes = bboxes(keepBox, :);
end