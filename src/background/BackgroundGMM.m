% A thin wrapper around vision.ForegroundDetector and vision.BlobAnalysis

classdef BackgroundGMM < BackgroundInterface
     properties (Hidden)
         detector;
         blob;
         shapeInserter;
     end
     properties (Hidden)  % constants

         % mask refinement
         fn_level = 22;
         fp_level = 1;

     end % properties
     
     methods
        function BS = BackgroundGMM (varargin)
            % parse and validate input
            parser = inputParser;
            addParameter(parser, 'num_training_frames', 3, @isscalar);
            addParameter(parser, 'initial_variance', 20, @isscalar);
            addParameter(parser, 'fn_level', 22, @isscalar);
            addParameter(parser, 'fp_level', 1, @isscalar);
            addParameter(parser, 'minimum_blob_area', 50, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            BS.fn_level = parsed.fn_level;
            BS.fp_level = parsed.fp_level;

            BS.detector = vision.ForegroundDetector(...
                   'NumTrainingFrames', parsed.num_training_frames, ...
                   'InitialVariance', parsed.initial_variance^2);
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
            parse (parser, image, varargin{:});
            parsed = parser.Results;

            % actual subtraction
            mask  = step(BS.detector, image);

            if parsed.denoise
                mask = denoiseMask(mask, BS.fn_level, BS.fp_level);
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
