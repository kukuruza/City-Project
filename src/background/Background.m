classdef Background
    % Background takes in a video frame by frame and generates 
    % A thin wrapper around vision.ForegroundDetector
    %
    % Can generate 

     properties
         % matlab underlying object
         detector;
         
         % one of two modes
         AdaptLearningRate;
         LearningRate;
         
         % mask refinement
         denoise;
         fn_level = 22;
         fp_level = 1;

     end % properties
     
     methods
        function BS = Background (varargin)
            % parse and validate input
            parser = inputParser;
            addParameter(parser, 'AdaptLearningRate', true, @islogical);
            addParameter(parser, 'NumTrainingFrames', 50, @isscalar);
            addParameter(parser, 'LearningRate', 0.005, @isscalar);
            addParameter(parser, 'MinimumBackgroundRatio', 0.9, @isscalar);
            addParameter(parser, 'NumGaussians', 2, @isscalar);
            addParameter(parser, 'InitialVariance', 15^2, @isscalar);
            addParameter(parser, 'denoise', false, @islogical);
            addParameter(parser, 'fn_level', 22, @isscalar);
            addParameter(parser, 'fp_level', 1, @isscalar);
            addParameter(parser, 'minimum_blob_area', 50, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            % used in both 'detector' init and the step
            BS.AdaptLearningRate = parsed.AdaptLearningRate;
            BS.LearningRate = parsed.LearningRate;
            
            % used if denoising is necessary
            BS.denoise = parsed.denoise;
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
        end
         
         
        function mask = step (BS, image)
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'image', @(x) ndims(x) == 3 && size(x,3) == 3);
            parse (parser, image);

            % actual subtraction
            if BS.AdaptLearningRate == true
                mask = step(BS.detector, image);
            else
                mask = step(BS.detector, image, BS.LearningRate);
            end

            if BS.denoise
                mask = denoiseMask(mask, BS.fn_level, BS.fp_level);
            end
         end
         
     end % methods

end
