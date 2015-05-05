classdef Candidates < CandidatesBase
    % Class to generate candidates for CNN's detection
    % Based on the geometry of the camera : pick the box based on the size
    % over the lanes
    
    properties
    end
    
    methods
        % Getting the candidate boxes, using size map of the given camera
        function bboxes = getCandidates (self, sizeMap, varargin)
            % Parameters to tune the way the boxes are generated
            parser = inputParser;
            addParameter(parser, 'minCarSize', 20); % Minimum size of car
            addParameter(parser, 'carAspectRatio', 1.2); % width/height ratio
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            % First segregrate the roads if possible
            clusters = bwlabel(sizeMap);
            clusterIds = unique(clusters);
            
            % Remove zero
            clusterIds(clusterIds == 0) = [];
            
            % Initialize bboxes to []
            bboxes = [];
            
            % For each cluster (lane / multiple lane)
            for i = 1:length(clusterIds)
                % Determine if single lane or multiple lanes
                laneMask = uint8(clusters == i);
                lane = sizeMap .* laneMask;

                laneSize = sum(laneMask, 2);
                [maxLaneSize, maxId] = max(laneSize);
               
                ratio = maxLaneSize/max(lane(maxId, :));
                
                % Assume single lane
                if(ratio < 2 && ratio > 0.5)
                    % Draw the boxes from approximately center (rnd) moving
                    % along the road
                    
                    % Find the first point of the lane
                    [~, startPt] = max(laneMask, [], 2);
                    
                    laneRows = laneSize > ratio * parsed.minCarSize;
                    %laneRows = maxVal > parsed.minCarSize;
                    
                    % Skip few rows
                    % laneRows() = ;
                    
                    % Y
                    y = 1:length(laneRows);
                    y = y(laneRows)';
                    
                    % X
                    % Adding some buffer (randomize?)
                    x = startPt(laneRows) + laneSize(laneRows)/3;
                    x = uint32(x); 
                    
                    % Height
                    linInds = sub2ind(size(sizeMap), y, x);
                    % figure(1); imagesc(sizeMap)
                    height = sizeMap(linInds);
                    
                    % Width
                    width = parsed.carAspectRatio * height;
                    bboxes = [bboxes; x y width height];
                    
                % Assume multiple lanes
                else
                    % Draw the boxes from anywhere random such that entire
                    % box stays within the road

                    % Roughly divide the road (based on the size)
                    noLanes = floor(ratio / 1.2);

                    % Finding the start point of the road
                    [~, startPt] = max(laneMask, [], 2);

                    % Finding the end point of the road
                    [~, endPt] = max(flip(laneMask, 2), [], 2);
                    endPt = size(laneMask, 2) + 1 - endPt;
                    
                    % Car size cutoff
                    laneRows = laneSize > ratio * parsed.minCarSize;
                    
                    % Finding the centers of the boxes
                    matrix = [linspace(1, 0, noLanes+2); ...
                                linspace(0, 1, noLanes+2)];
                    matrix = matrix(:, 2:end-1); % Ignore the start / end
                    centers = [startPt, endPt] * matrix;
                    
                    % y (need to be adjusted for getting top left corner)
                    y = 1:length(laneRows);
                    y = y(laneRows)';
                    yMiddle = uint32(repmat(y, [noLanes, 1]));
                    
                    % x (need to be adjusted for getting top left corner)
                    xMiddle = uint32(reshape(centers(laneRows, :), [], 1));
                    
                    % height
                    linInds = sub2ind(size(sizeMap), yMiddle, xMiddle);
                    height = uint32(sizeMap(linInds));
                    
                    % width
                    width = parsed.carAspectRatio * height;
                    
                    % Adjusting the rectangle
                    x = uint32(xMiddle - width/2);
                    y = uint32(yMiddle - height/2);
                    
                    % Bounding boxes
                    bboxes = [bboxes; x y width height];
                end 
            end
        end
    end     
end