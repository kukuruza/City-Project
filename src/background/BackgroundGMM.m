% A thin wrapper around vision.ForegroundDetector and vision.BlobAnalysis

classdef BackgroundGMM < BackgroundInterface
     properties
         detector;
         blob;
         shapeInserter;

         % one of two modes
         AdaptLearningRate;
         LearningRate;
         
         % mask refinement
         fn_level = 22;
         fp_level = 1;
         
         % store result after every step
         result = [];

     end % properties
     
     methods
        function BS = BackgroundGMM (varargin)
            % parse and validate input
            parser = inputParser;
            addParameter(parser, 'AdaptLearningRate', true, @islogical);
            addParameter(parser, 'NumTrainingFrames', 50, @isscalar);
            addParameter(parser, 'LearningRate', 0.005, @isscalar);
            addParameter(parser, 'MinimumBackgroundRatio', 0.9, @isscalar);
            addParameter(parser, 'NumGaussians', 2, @isscalar);
            addParameter(parser, 'InitialVariance', 15^2, @isscalar);
            addParameter(parser, 'fn_level', 22, @isscalar);
            addParameter(parser, 'fp_level', 1, @isscalar);
            addParameter(parser, 'minimum_blob_area', 50, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            BS.AdaptLearningRate = parsed.AdaptLearningRate;
            BS.LearningRate = parsed.LearningRate;
            BS.fn_level = parsed.fn_level;
            BS.fp_level = parsed.fp_level;

            if BS.AdaptLearningRate == true
                BS.detector = vision.ForegroundDetector(...
                       'AdaptLearningRate', true, ...
                       'NumTrainingFrames', parsed.NumTrainingFrames, ...
                       'LearningRate', parsed.LearningRate, ...
                       'MinimumBackgroundRatio', parsed.MinimumBackgroundRatio, ...
                       'NumGaussians', parsed.NumGaussians, ...
                       'InitialVariance', parsed.InitialVariance);
            else
                BS.detector = vision.ForegroundDetector(...
                       'AdaptLearningRate', false, ...
                       'MinimumBackgroundRatio', parsed.MinimumBackgroundRatio, ...
                       'NumGaussians', parsed.NumGaussians, ...
                       'InitialVariance', parsed.InitialVariance);
            end
                
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
            addParameter(parser, 'denoise', false, @islogical);
            parse (parser, image, varargin{:});
            parsed = parser.Results;

            % actual subtraction
            if BS.AdaptLearningRate == true
                mask = step(BS.detector, image);
            else
                mask = step(BS.detector, image, BS.LearningRate);
            end

            if parsed.denoise
                mask = denoiseMask(mask, BS.fn_level, BS.fp_level);
            end
            
            % store result
            BS.result = mask;
         end
         
         
        % bbox [x,y,w,h] 
         function bboxes = mask2bboxes (BS, mask)
             bboxes = step(BS.blob, mask);
         end 
         
         
         function im_out = drawboxes (BS, image, bboxes)
             bboxes = [bboxes(:,1), bboxes(:,2), bboxes(:,3), bboxes(:,4)];
             im_out = step(BS.shapeInserter, image, bboxes);
         end

         
         % saving vision.ForegroundDetector is not trivial
%          function save (BS, path)
%             % parse and validate input
%             parser = inputParser;
%             addRequired(parser, 'path', @(x) exist(fileparts(x), 'dir'));
%             parse (parser, path);
%             
%             feature('SystemObjectsFullSaveLoad',1);
%             BS.
% 
%          end
             
         
     end % methods

end
