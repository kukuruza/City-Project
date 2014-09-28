% A thin wrapper around vision.ForegroundDetector and vision.BlobAnalysis

classdef BackgroundSubtractor < handle
     properties (Hidden)
         detector;
         blob;
         shapeInserter;
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
                   'CentroidOutputPort', false, 'AreaOutputPort', false, ...
                   'BoundingBoxOutputPort', true, ...
                   'MinimumBlobAreaSource', 'Property', ...
                   'MinimumBlobArea', MinimumBlobArea_);
               
             BS.shapeInserter = vision.ShapeInserter('BorderColor','White');
         end

         function [mask, ROIs, frame_out] = subtract (BS, frame)
             mask  = step(BS.detector, frame);
             bboxes = step(BS.blob, mask);
             frame_out = step(BS.shapeInserter, frame, bboxes); % draw bounding boxes around cars
             
             % bbox {x,y,w,h} to ROI {x1,y1,x2,y2}
             ROIs = [bboxes(:,1), bboxes(:,2), bboxes(:,1)+bboxes(:,3), bboxes(:,2)+bboxes(:,4)];
         end
     end % methods

end