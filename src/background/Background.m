% A thin wrapper around vision.ForegroundDetector and vision.BlobAnalysis

classdef Background < BackgroundInterface
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
        function BS = Background (varargin) % see interface
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
         
         

         % bbox [x,y,w,h] 
         function [mask, bboxes] = subtract (BS, frame)
             mask  = step(BS.detector, frame);
             bboxes = step(BS.blob, mask);

             %ROIs
             %imshow([frame 255*uint8(mask)]);
             %waitforbuttonpress
         end
         
         
         % add more foreground and remove noise
         function [mask, bboxes] = subtractAndDenoise (BS, frame)
             mask  = step(BS.detector, frame);
             mask = denoiseMask(mask, BS.fn_level, BS.fp_level);
             
             bboxes = step(BS.blob, mask);
         end
         
         
         % when mask from the previus function is changed and bboxes wanted
         function bboxes = mask2bboxes (BS, mask)
             bboxes = step(BS.blob, mask);
         end 
         
         
         function im_out = drawboxes (BS, im, bboxes)
             bboxes = [bboxes(:,1), bboxes(:,2), bboxes(:,3), bboxes(:,4)];
             im_out = step(BS.shapeInserter, im, bboxes);
         end
         
         
         % If there is just one car in the image detect it
         % Returns [] if there is not exactly one car
         function [bbox, certainty] = getSingleCar (BS, frame)
             % default is failure
             bbox = [];
             certainty = 0;
             
             % get with the usual subtract
             [~, bboxes] = subtract (BS, frame);
             if size(bboxes,1) ~= 1, return, end
             
             % TODO: get more advanced accuracy
             bbox = bboxes;
             certainty = 1;
         end
         
     end % methods

end
