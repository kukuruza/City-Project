classdef CandidatesSizemap < CandidatesBase
    % Class to generate candidates for CNN's detection
    % Based on the geometry of the camera : pick the box based on the size
    % over the lanes
    
    properties (Hidden)
        mapSize
        minCarSize       % minimum width of car
        carAspectRatio   % width/height ratio
        interval         % interval between candidate bboxes, pxl
        
        bboxes  % generated at the time of contructing the object
    end
    
    methods
        
        function self = CandidatesSizemap (mapSize, varargin)
            % Parameters to tune the way the boxes are generated
            parser = inputParser;
            addRequired (parser, 'mapSize', @ismatrix);
            addParameter(parser, 'minCarSize', 10, @isscalar);
            addParameter(parser, 'carAspectRatio', 1.33, @isscalar); 
            addParameter(parser, 'interval', 5, @isscalar);
            
            parse (parser, mapSize, varargin{:});
            parsed = parser.Results;
            
            self.mapSize        = parsed.mapSize;
            self.minCarSize     = parsed.minCarSize;
            self.carAspectRatio = parsed.carAspectRatio;
            self.interval       = parsed.interval;
            
            % First segregrate the roads if possible
            clusters = bwlabel(self.mapSize);
            clusterIds = unique(clusters);
            
            % Remove zero
            clusterIds(clusterIds == 0) = [];
            
            % Initialize bboxes to []
            self.bboxes = [];
            
            % For each cluster (lane / multiple lane)
            for i = 1:length(clusterIds)
                % Determine if single lane or multiple lanes
                laneMask = uint8(clusters == i);
                lane = self.mapSize .* laneMask;

                laneSize = sum(laneMask, 2);
                [maxLaneSize, maxId] = max(laneSize);
               
                ratio = maxLaneSize/max(lane(maxId, :));
                
                % Assume single lane
                if(ratio < 2 && ratio > 0.5)
                    % Draw the boxes from approximately center (rnd) moving
                    % along the road
                    
                    % Find the first point of the lane
                    [~, startPt] = max(laneMask, [], 2);
                    
                    laneRows = laneSize > ratio * self.minCarSize;
                    %laneRows = maxVal > self.minCarSize;
                    
                    % Skip few rows
                    % laneRows() = ;
                    
                    % Y
                    y = 1:length(laneRows);
                    y = uint32(y(laneRows)');
                    
                    % X
                    % Adding some buffer (randomize?)
                    x = startPt(laneRows) + laneSize(laneRows)/3;
                    x = uint32(x); 
                    
                    % Height
                    linInds = sub2ind(size(self.mapSize), y, x);
                    % figure(1); imagesc(self.mapSize)
                    height = uint32(self.mapSize(linInds));
                    
                    % Width
                    width = uint32(self.carAspectRatio * height);

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
                    laneRows = laneSize > ratio * self.minCarSize;
                    
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
                    linInds = sub2ind(size(self.mapSize), yMiddle, xMiddle);
                    height = uint32(self.mapSize(linInds));
                    
                    % width
                    width = uint32(self.carAspectRatio * height);
                    
                    % Adjusting the rectangle
                    x = uint32(xMiddle - width/2);
                    y = uint32(yMiddle - height/2);
                end
                
                % Dealing with border cases -- ignore them
                % image size
                imSize = size(self.mapSize);
                % Getting the border cases
                removeId =  (x < 1) | (x > imSize(2)) | ...
                            (y < 1) | (y > imSize(1)) | ...
                            (x + width > imSize(2)) | ...
                            (y + height > imSize(1)) | ...
                            height < 1 | width < 1;
            
                retainId = ~removeId;
                x       = x(retainId);
                y       = y(retainId);
                width   = width(retainId);
                height  = height(retainId);

                % assertion inside is violated if bbox is out of bounds
                % Assertion is for each box, not a batch !
                for j = 1:size(x, 1)
                    bbox2roi([x(j) y(j) width(j) height(j)]);
                end
                
                self.bboxes = [self.bboxes; x y width height];        
            end
            self.bboxes = self.bboxes(1:self.interval:size(self.bboxes,1), :);
        end
        
        % Getting the candidate boxes, using size map of the given camera
        function bboxes = getCandidates (self, varargin)
            bboxes = self.bboxes;
        end
        
    end
end