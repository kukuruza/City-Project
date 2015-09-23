% implementation of CarDetectorInterface that allows different detectors for clusters

classdef FrombackDetector < CarDetectorBase
    properties

        blob % matlab object to get bboxes from mask

        % verbose = 0  no info
        %         = 1  how many filtered
        %         = 2  assign car indices to names, print indices at filter
        verbose;
        
        % debugging
        %disable removing cars after filtering
        noFilter = false;
        
        Heght2WidthLimits = [0.5 1.2];
        %SparseDist = 0.0;
        DensitySigma = 0.7;
        DensityRatio = 2.0;
        DistToBorder = 20;
        ExpandPerc = 0.0;

    end % properties
    methods (Hidden)
        
        function indices = findByStatus (~, statuses, name)
            indices = find(not(cellfun('isempty', strfind(statuses, name))));
        end
        
        function indices = filterByStatus (~, statuses, name)
            indices = find(cellfun('isempty', strfind(statuses, name)));
        end
        
        
        % filter by bbox proportions
        function statuses = filterByProportion (self, cars, statuses)
            for i = 1 : length(cars)
                if ~strcmp(statuses{i}, 'ok'), continue, end
                proportion = double(cars(i).bbox(4)) / double(cars(i).bbox(3));
                if proportion < self.Heght2WidthLimits(1) || proportion > self.Heght2WidthLimits(2)
                    if self.verbose > 1
                        fprintf ('    car %d - bad ratio %f\n', i, proportion); 
                    end
                    statuses{i} = 'bad ratio';
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

        
        function statuses = filterBySparsity (self, mask, cars, statuses)
            parser = inputParser;
            addRequired(parser, 'mask', @(x) islogical(x) && ismatrix(x));
            addRequired(parser, 'cars', @(x) isempty(x) || isa(x, 'Car'));
            addRequired(parser, 'statuses', @(x) isvector(x));
            parse (parser, mask, cars, statuses);

            whites = ones(size(mask,1),size(mask,2));
            for i = 1 : length(cars)
                center = cars(i).getCenter();
                sigma = (cars(i).bbox(3) + cars(i).bbox(4)) / 2 * self.DensitySigma;
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
                    statuses{i} = 'too dense';
                end
            end
        end
        
        
%         % filter too dense cars in the image
%         function statuses = filterBySparsity (self, cars, statuses)
%             for i = 1 : length(cars)
%                 center = cars(i).getCenter(); % [y x]
%                 expectedSize = self.sizeMap(center(1), center(2));
%                 for k = 1 : length(cars)
%                     if ~strcmp(statuses{i}, 'ok'), continue, end
%                     if i ~= k && dist(center, cars(k).getCenter()') < expectedSize * self.SparseDist
%                         if self.verbose > 1, fprintf ('    car %d - too dense\n', i); end
%                         statuses{i} = 'too dense'; 
%                         break
%                     end
%                 end
%             end
%         end
        
        
        % filter too dense cars in the image
%         function statuses = filterBySparsity2 (self, cars, statuses)
%             for i = 1 : length(cars)
%                 pdf = normpdf
%         end
        
        % filter those too close to the border
        function statuses = filterByBorder (self, cars, statuses)
            % need at least DistToBorder pixels to border
            sz = size(self.sizeMap);
            for i = 1 : length(cars)
                if ~strcmp(statuses{i}, 'ok'), continue, end
                roi = cars(i).getROI();
                distToBorder = min([roi(1:2), sz(1)-roi(3), sz(2)-roi(4)]);
                if distToBorder < self.DistToBorder
                    if self.verbose > 1, 
                        fprintf ('    car %d - too close to border = %d\n', i, distToBorder); 
                    end
                    statuses{i} = 'close to border'; 
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

        
        function setVerbosity (self, verbose)
            self.verbose = verbose;
        end

        
        function cars = detect (self, img, mask)
            parser = inputParser;
            addRequired(parser, 'img',  @iscolorimage);
            addRequired(parser, 'mask', @(x) ismatrix(x) && islogical(x));
            parse (parser, img, mask);
            assert (size(img,1) == size(mask,1) && size(img,2) == size(mask,2));

            if self.verbose > 1, fprintf ('FrombackDetector\n'); end

            bboxes = step(self.blob, mask);

            N = size(bboxes,1);
            cars = Car.empty;
            statuses = cell(N,1);
            for i = 1 : N
                cars(i) = Car('bbox', bboxes(i,:), 'name', sprintf('%d',i));
                statuses{i} = 'ok';
            end
            cars = cars';
            %     mask = imerode (mask, strel('disk', 2));
            %     mask = imdilate(mask, strel('disk', 2));

             % expand boxes
            for i = 1 : N
                cars(i).bbox = expandBboxes (cars(i).bbox, self.ExpandPerc, img);
            end
            
            % filters specific for backimagedetector
            if ~self.noFilter
                statuses = self.filterByProportion (cars, statuses);
                statuses = self.filterBySparsity (mask, cars, statuses);
                %statuses = self.filterByBorder (cars, statuses);
            end
            
            if self.verbose
                fprintf ('FrombackDetector\n');
                fprintf ('    filtered proportions:  %d\n', ...
                    length(self.findByStatus(statuses, 'bad ratio')));
                fprintf ('    filtered too dense:    %d\n', ...
                    length(self.findByStatus(statuses, 'too dense')));
                fprintf ('    filtered close border: %d\n', ...
                    length(self.findByStatus(statuses, 'close to border')));
                fprintf ('    left ok:               %d\n', ...
                    length(self.findByStatus(statuses, 'ok')));
            end

            % filter bad cars
            cars (self.filterByStatus(statuses, 'ok')) = [];
        end

    end % methods
end
