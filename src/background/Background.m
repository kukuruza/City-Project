% A thin wrapper around vision.ForegroundDetector and vision.BlobAnalysis

classdef Background < BackgroundInterface
     properties (Hidden)
         detector;
         blob;
         shapeInserter;
     end
     properties  % constants
         
         % background subtraction
         num_training_frames = 3;
         initial_variance = 20;
         
         % mask refinement
         fn_level = 22;
         fp_level = 1;
         
         % extracting bounding boxes
         minimum_blob_area = 50;
         
     end % properties
     
     methods
         function BS = Background ()
             BS.detector = vision.ForegroundDetector(...
                   'NumTrainingFrames', BS.num_training_frames, ...
                   'InitialVariance', BS.initial_variance^2);
             BS.blob = vision.BlobAnalysis(...
                   'CentroidOutputPort', false, ...
                   'AreaOutputPort', false, ...
                   'BoundingBoxOutputPort', true, ...
                   'MinimumBlobAreaSource', 'Property', ...
                   'MinimumBlobArea', BS.minimum_blob_area);
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
