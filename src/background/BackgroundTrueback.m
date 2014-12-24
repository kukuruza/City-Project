% Just subtract a provided image

classdef BackgroundTrueback < BackgroundInterface
    properties (Hidden)
        blob;
        shapeInserter;

        % background image (without cars)
        back_image;
        black_threshold = 5;

        % mask refinement (merging close boxes)
        denoise_level
        merge_level

        % for adjusting colors
        road_mask

    end % properties
    
    methods (Hidden)
        function image = adjustColors (BS, image)
            image1 = image(:,:,1);
            image1(~BS.road_mask) = 0;
            imshow(image1)
            pause
            
            for ch = 1 : 3
                channel = image(:,:,ch);
                assert (all(size(BS.road_mask) == size(channel)));
                back_image_ch = BS.back_image(:,:,ch);
                hgram = imhist (back_image_ch(BS.road_mask));
                figure(2)
                plot(imhist (channel(BS.road_mask)));
                image(:,:,ch) = histeq(channel, hgram);
                figure(3)
                plot(hgram);
                figure(1)
            end
            
            image1 = image(:,:,1);
            image1(~BS.road_mask) = 0;
            imshow(image1)
            pause
        end
    end
     
    methods
        function BS = BackgroundTrueback (varargin) % see interface
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'back_image_path', @ischar);
            addRequired(parser, 'geometry', @(x) isa(x, 'GeometryEstimator'));
            addParameter(parser, 'black_threshold', 20, @isscalar);
            addParameter(parser, 'denoise_level', 1, @isscalar);
            addParameter(parser, 'merge_level', 10, @isscalar);
            addParameter(parser, 'minimum_blob_area', 50, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            BS.black_threshold = parsed.black_threshold;
            BS.denoise_level = parsed.denoise_level;            
            BS.merge_level = parsed.merge_level;

            % get values from geometry
            BS.road_mask = parsed.geometry.getCameraRoadMap() > 0;
            
            % load clear image (without cars)
            assert (exist(parsed.back_image_path, 'file') == 2);
            BS.back_image = imread(parsed.back_image_path);
            assert (ndims(BS.back_image) == 3 && size(BS.back_image,3));

            BS.blob = vision.BlobAnalysis(...
                   'CentroidOutputPort', false, ...
                   'AreaOutputPort', false, ...
                   'BoundingBoxOutputPort', true, ...
                   'MinimumBlobAreaSource', 'Property', ...
                   'MinimumBlobArea', parsed.minimum_blob_area);
            BS.shapeInserter = vision.ShapeInserter(...
                   'BorderColor','White', ...
                   'Fill',true, ...
                   'FillColor','White', ...
                   'Opacity',0.2);
        end
         
         

        function mask = subtract (BS, image, varargin)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'image', @(x) ndims(x) == 3 && size(x,3) == 3);
            addParameter(parser, 'denoise', true, @islogical);
            addParameter(parser, 'merge', true, @islogical);
            parse (parser, image, varargin{:});
            parsed = parser.Results;
            
            % adjust histogram
            %image = BS.adjustColors(image);

            % actual subtraction
            mask = abs(image - BS.back_image);
            mask = rgb2gray(mask);
            mask = (mask > BS.black_threshold);

            if parsed.denoise
                seDenoise = strel('disk', BS.denoise_level);
                mask = imerode(mask, seDenoise);
            end
            if parsed.merge
                seMerge = strel('disk', BS.merge_level);
                mask = imdilate(mask, seMerge);
                mask = imerode(mask, seMerge);
            end
         end
         
         
        % bbox [x,y,w,h] 
         function bboxes = mask2bboxes (BS, mask)
             bboxes = step(BS.blob, mask);
         end 
         
         
         function im_out = drawboxes (BS, image, bboxes)
             bboxes = [bboxes(:,1), bboxes(:,2), bboxes(:,3), bboxes(:,4)];
             im_out = step(BS.shapeInserter, image, bboxes);
         end
         
         
         % If there is just one car in the image detect it
         % Returns [] if there is not exactly one car
         function [bbox, certainty] = getSingleCar (BS, image)
             % default is failure
             bbox = [];
             certainty = 0;
             
             % get with the usual subtract
             [~, bboxes] = subtract (BS, image);
             if size(bboxes,1) ~= 1, return, end
             
             % TODO: get more advanced accuracy
             bbox = bboxes;
             certainty = 1;
         end
         
     end % methods

end
