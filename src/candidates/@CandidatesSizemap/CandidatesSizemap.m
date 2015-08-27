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
        
        % Threshold for checking for background occupancy to filter
        % candidates
        occupancyThreshold;
    end
    
    methods
        function self = CandidatesSizemap (mapSize, varargin)
            % Parameters to tune the way the boxes are generated
            parser = inputParser;
            addRequired (parser, 'mapSize', @ismatrix);
            addParameter(parser, 'minCarSize', 10, @isscalar);
            addParameter(parser, 'carAspectRatio', 1.33, @isscalar); 
            addParameter(parser, 'interval', 5, @isscalar);
            addParameter(parser, 'occupancy', 0.05, @isscalar);

            parse (parser, mapSize, varargin{:});
            parsed = parser.Results;

            self.mapSize        = parsed.mapSize;
            self.minCarSize     = parsed.minCarSize;
            self.carAspectRatio = parsed.carAspectRatio;
            self.interval       = parsed.interval;
            self.occupancyThreshold = parsed.occupancy;
            
            % Initialize the candidates
            self = self.initializeCandidates();
        end
        
        % Initializing the candidates
        self = initializeCandidates(self);

        % Filter candidates by candidate
        filteredBoxes = filterCandidatesBackground(self, bboxes, background);
        
        % Getting the candidate boxes, using size map of the given camera
        function bboxes = getCandidates (self, varargin)
            bboxes = self.bboxes;
        end
        
    end
end