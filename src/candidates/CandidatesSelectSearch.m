classdef CandidatesSelectSearch < CandidatesBase
    %
    % Box Candidates strategy by Selective Search 
    %

    properties
        % Parameters. Note that this controls the number of hierarchical
        % segmentations which are combined.
        colorTypes = {'Hsv', 'Lab', 'RGI', 'H', 'Intensity'};
        colorType;

        % Here you specify which similarity functions to use in merging
        simFunctionHandles = {@SSSimColourTextureSizeFillOrig, @SSSimTextureSizeFill, @SSSimBoxFillOrig, @SSSimSize};

        % Thresholds for the Felzenszwalb and Huttenlocher segmentation algorithm.
        % Note that by default, we set minSize = k, and sigma = 0.8.
        k = 200; % controls size of segments of initial segmentation. 
        minSize = 200;
        sigma = 0.8;
        
        % severe filter with sizemap
        mapSize;
        SizeAllowance = [0.3, 3];
        
        verbose;
    end
    
    methods
        % Getting the candidate boxes
        function bboxes = getCandidates (self, varargin)
            parser = inputParser;
            addParameter(parser, 'image', [], @iscolorimage);
            parse (parser, varargin{:});
            parsed = parser.Results;
            assert (~isempty(parsed.image));
            
            % use selective serach
            rois = Image2HierarchicalGrouping (parsed.image, ...
                self.sigma, self.k, self.minSize, self.colorType, self.simFunctionHandles);
            rois = BoxRemoveDuplicates(rois);

            % from roi=[y1,x1,y2,x2] to bbox=[x1,y1,width,height]
            bboxes = zeros(size(rois));
            for i = 1 : size(rois,1)
                bboxes(i,:) = roi2bbox(rois(i,:));
            end
            
            % filter with sizeMap
            for i = size(bboxes,1) : -1 : 1
                bbox = bboxes(i,:);
                bc = getBottomCenter(bbox);
                sz = (bbox(3) + bbox(4)) / 2;
                if sz < self.SizeAllowance(1) * self.mapSize(bc(1), bc(2)) || ...
                   sz > self.SizeAllowance(2) * self.mapSize(bc(1), bc(2))
                     bboxes(i,:) = [];
                end
            end 
        end
        
        function self = CandidatesSelectSearch (varargin)
            parser = inputParser;
            addParameter(parser, 'verbose', 0, @isscalar);
            addParameter(parser, 'k', 200, @isscalar);
            addParameter(parser, 'minSize', 200, @isscalar);
            addParameter(parser, 'sigma', 0.8, @isscalar);
            addParameter(parser, 'simFunctions', [1,2]);
            addParameter(parser, 'colorType', 1);
            addParameter(parser, 'mapSize', []);
            addParameter(parser, 'SizeAllowance', [0.3, 3], @(x) isvector(x) && length(x) == 2);
            addParameter(parser, 'occupancy', 0.05, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;

            self.occupancyThreshold = parsed.occupancy;

            assert (~isempty(parsed.mapSize));
            
            addpath (genpath(fullfile(getenv('CITY_PATH'), '3rd-party/SelectiveSearchCodeIJCV')));
            
            self.verbose = parsed.verbose;
            self.k = parsed.k;
            self.minSize = parsed.minSize;
            self.sigma = parsed.sigma;
            self.simFunctionHandles = self.simFunctionHandles(parsed.simFunctions);
            self.colorType = self.colorTypes{parsed.colorType};
            self.mapSize = parsed.mapSize;
            self.SizeAllowance = parsed.SizeAllowance;
        end
    end
end
