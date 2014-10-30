% A thin wrapper around vision.ForegroundDetector and vision.BlobAnalysis

classdef BackgroundSubtractor < handle
     properties (Hidden)
         detector;
         blob;
         shapeInserter;
     end
     properties  % constants
         
         % background subtraction
         num_training_frames = 5;
         initial_variance = 30;
         
         % mask refinement
         fn_level = 15;
         fp_level = 1;
         
         % extracting bounding boxes
         minimum_blob_area = 50;
         
     end % properties
     
     methods
         function BS = BackgroundSubtractor ()
             BS.detector = vision.ForegroundDetector(...
                   'NumTrainingFrames', BS.num_training_frames, ...
                   'InitialVariance', BS.initial_variance^2);
             BS.blob = vision.BlobAnalysis(...
                   'CentroidOutputPort', false, ...
                   'AreaOutputPort', false, ...
                   'BoundingBoxOutputPort', true, ...
                   'MinimumBlobAreaSource', 'Property', ...
                   'MinimumBlobArea', BS.minimum_blob_area);
             BS.shapeInserter = vision.ShapeInserter('BorderColor','White');
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
             mask = denoiseForegroundMask(mask, BS.fn_level, BS.fp_level);
             
             % alternative function to denoiseForegroundMask
             %mask = gaussFilterMask(mask, 20, 0.1);
             
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
     end % methods

end
