% Just subtract a provided image

classdef BackgroundSingle < BackgroundInterface
     properties (Hidden)
         blob;
         shapeInserter;
     end
     properties (Hidden)  % constants

         back_frame;
         
         % mask refinement
         black_threshold = 5;

         % mask refinement (merging close boxes)
         seErode;
         seDilate;
         
     end % properties
     
     methods
        function BS = BackgroundSingle (varargin) % see interface
            % parse and validate input
            parser = inputParser;
            addRequired(parser, 'back_frame_path', @ischar);
            addParameter(parser, 'black_threshold', 20, @isscalar);
            addParameter(parser, 'erode_level', 1, @isscalar);
            addParameter(parser, 'dilate_level', 10, @isscalar);
            addParameter(parser, 'minimum_blob_area', 50, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            BS.black_threshold = parsed.black_threshold;
            BS.seErode = strel('disk', parsed.erode_level);
            BS.seDilate = strel('disk', parsed.dilate_level);
            
            assert (exist(parsed.back_frame_path, 'file') == 2);
            BS.back_frame = imread(parsed.back_frame_path);

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
             assert (ndims(frame) == ndims(BS.back_frame));
             mask = abs(frame - BS.back_frame);
             if ndims(mask) == 3, mask = rgb2gray(mask); end
             mask(mask < BS.black_threshold) = 0;
             
             bboxes = step(BS.blob, mask > 0);

             %ROIs
             %imshow([frame 255*uint8(mask)]);
             %waitforbuttonpress
         end
         
         
         % add more foreground and remove noise
         function [mask, bboxes] = subtractAndDenoise (BS, frame)
             [mask, ~] = BS.subtract (frame);
             
             % remove noise
             mask = imerode(mask, BS.seErode);

             % merge close boxes
             mask = imdilate(mask, BS.seDilate);
             mask = imerode(mask, BS.seDilate);

             bboxes = step(BS.blob, mask > 0);
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
