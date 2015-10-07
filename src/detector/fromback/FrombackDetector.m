% implementation of CarDetectorInterface that allows different detectors for clusters

classdef FrombackDetector < CarDetectorBase
    properties

        blob % matlab object to get bboxes from mask

        % verbose = 0  no info
        %         = 1  how many filtered
        %         = 2  assign car indices to names, print indices at filter
        
        % debugging
        %disable removing cars after filtering
        noFilter = false;
        
        Heght2WidthLimits = [0.5 1.2];
        %SparseDist = 0.0;
        DensitySigma = 0.7;
        DensityRatio = 2.0;
        ExpandPerc = 0.1;

    end % properties
    methods (Hidden)
        
        % filter by bbox proportions
        function filterByProportion (self, cars)
            for i = 1 : length(cars)
                proportion = double(cars(i).bbox(4)) / double(cars(i).bbox(3));
                if proportion < self.Heght2WidthLimits(1) || proportion > self.Heght2WidthLimits(2)
                    if self.verbose > 1, fprintf ('    car %d - bad ratio %f\n', i, proportion); end
                    cars(i).score = 0;
                end
            end
        end

        
        function result = filterOnce (~, mask, center, sz, kernel)
            assert (ismatrix(mask));
            mask = double(mask);
            kernel = kernel (max(1, sz-center(1)+2) : min(sz*2+1, sz+1+size(mask,1)-center(1)), ...
                             max(1, sz-center(2)+2) : min(sz*2+1, sz+1+size(mask,2)-center(2)));
            mask = mask (max(1, center(1)-sz) : min(center(1)+sz, size(mask,1)), ...
                         max(1, center(2)-sz) : min(center(2)+sz, size(mask,2)));
            result = mask .* kernel;
            %imagesc(result);
            %colormap('gray')
            %pause;
            result = sum(result(:));
        end

        
        function filterBySparsity (self, mask, cars)
            parser = inputParser;
            addRequired(parser, 'mask', @(x) islogical(x) && ismatrix(x));
            addRequired(parser, 'cars', @(x) isempty(x) || isa(x, 'Car'));
            parse (parser, mask, cars);

            whites = ones(size(mask,1),size(mask,2));
            for i = 1 : length(cars)
                if cars(i).score == 0, continue; end
                
                center = cars(i).getCenter();
                sigma = double((cars(i).bbox(3) + cars(i).bbox(4)) / 2 * self.DensitySigma);
                sz = floor(sigma * 2.5);
                gaussKernel = fspecial('gaussian', sz * 2 + 1, sigma);
                
                roi = bbox2roi(cars(i).bbox);
                maskInside = zeros (size(mask,1), size(mask,2));
                maskInside(roi(1):roi(3), roi(2):roi(4)) = mask(roi(1):roi(3), roi(2):roi(4));
                insideResponse = self.filterOnce (maskInside, center, sz, gaussKernel);
                whitesInside = zeros (size(whites,1), size(whites,2));
                whitesInside(roi(1):roi(3), roi(2):roi(4)) = 1;
                insideNorm = self.filterOnce (whitesInside, center, sz, gaussKernel);
                assert (insideNorm ~= 0);
                insideDensity = insideResponse / insideNorm;
                %fprintf ('insideDensity %f, insideNorm %f\n', insideDensity, insideNorm);

                roi = bbox2roi(cars(i).bbox);
                maskOutside = mask;
                maskOutside(roi(1):roi(3), roi(2):roi(4)) = 0;
                outsideResponse = self.filterOnce (maskOutside, center, sz, gaussKernel);
                whitesOutside = whites;
                whitesOutside(roi(1):roi(3), roi(2):roi(4)) = 0;
                outsideNorm = self.filterOnce (whitesOutside, center, sz, gaussKernel);
                assert (outsideNorm ~= 0);
                outsideDensity = outsideResponse / outsideNorm;
                %fprintf ('outsideDensity %f, outsideNorm %f\n', outsideDensity, outsideNorm);
                
                density = insideDensity / outsideDensity;
%                 if self.verbose > 1
%                     fprintf ('    car %d - density %f\n', i, density); 
%                 end
                if density < self.DensityRatio
                    if self.verbose > 1
                        fprintf ('    car %d - density %f\n', i, density); 
                    end
                    cars(i).score = 0;
                else
                    cars(i).score = atan(density / self.DensityRatio) / (pi/2);
                end
            end
        end
        
        
    end
    methods
        
        function self = FrombackDetector (varargin)
            parser = inputParser;
            addParameter(parser, 'minimum_blob_area', 50, @isscalar);
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            self.verbose = parsed.verbose;
            
            self.blob = vision.BlobAnalysis(...
                   'CentroidOutputPort', false, ...
                   'AreaOutputPort', false, ...
                   'BoundingBoxOutputPort', true, ...
                   'MinimumBlobAreaSource', 'Property', ...
                   'MinimumBlobArea', parsed.minimum_blob_area);
        end

        
        function cars = detect (self, mask)
            parser = inputParser;
            addRequired(parser, 'mask', @(x) ismatrix(x) && islogical(x));
            parse (parser, mask);

            if self.verbose > 1, fprintf ('FrombackDetector\n'); end

            bboxes = step(self.blob, mask);

            N = size(bboxes,1);
            cars = Car.empty;
            for i = 1 : N
                cars(i) = Car('bbox', bboxes(i,:), 'name', 'object', 'score', 1);
            end
            cars = cars';

            % filters specific for backimagedetector
            if ~self.noFilter
                self.filterByProportion (cars);
                self.filterBySparsity (mask, cars);
            end

            % expand boxes
            for i = 1 : N
                cars(i).bbox = expandBboxes (cars(i).bbox, self.ExpandPerc, mask);
            end
            
            % filter bad cars
            scores = zeros(N,1);
            for i = 1 : N, scores(i) = cars(i).score; end
            cars (scores == 0) = [];
        end

    end % methods
end
