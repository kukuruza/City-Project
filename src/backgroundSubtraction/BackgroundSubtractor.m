% A thin wrapper around vision.ForegroundDetector and vision.BlobAnalysis

classdef BackgroundSubtractor < handle
     properties (Hidden)
         detector;
         blob;
         shapeInserter;
         
         % those are specific to cameras and should be learned and set
         fn_level = 15;
         fp_level = 1;
     end % properties
     
     methods
         function BS = BackgroundSubtractor (NumTrainingFrames_, InitialVariance_, MinimumBlobArea_)
             
             % default parameters
             if ~exist('NumTrainingFrames_','var') || isempty(NumTrainingFrames_)
                 NumTrainingFrames_ = 5;
             end
             if ~exist('InitialVariance_','var') || isempty(InitialVariance_)
                 InitialVariance_ = 30;
             end
             if ~exist('MinimumBlobArea_','var') || isempty(MinimumBlobArea_)
                 MinimumBlobArea_ = 50;
             end

             BS.detector = vision.ForegroundDetector(...
                   'NumTrainingFrames', NumTrainingFrames_, ...
                   'InitialVariance', InitialVariance_^2);

             BS.blob = vision.BlobAnalysis(...
                   'CentroidOutputPort', false, ...
                   'AreaOutputPort', false, ...
                   'BoundingBoxOutputPort', true, ...
                   'MinimumBlobAreaSource', 'Property', ...
                   'MinimumBlobArea', MinimumBlobArea_);
               
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
