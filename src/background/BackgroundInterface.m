% Interface for the Background class
%
% Intended for USERS of the Background class to look up function names
%   Users don't need to see function implementations, only signatures

classdef BackgroundInterface < handle
    methods (Abstract)

         % Get noisy foreground mask and optionally boxes (bbox [x,y,w,h])
         %
         %function [mask, bboxes] = 
         subtract (BS, frame)
         
         % The same, but with increased foreground recall and removed noise
         %
         %function [mask, bboxes] = 
         subtractAndDenoise (BS, frame)
         
         % When mask from the previus function is changed and bboxes wanted
         %
         %function bboxes = 
         mask2bboxes (BS, mask)
         
         % Draw provided boxes in the provided image
         %
         %function im_out = 
         drawboxes (BS, im, bboxes)
         
         % If there is just one car in the image detect it
         % Returns [] if there is more than one car
         %
         %function [bbox, certainty] = 
         getSingleCar (BS, frame)

    end % methods
end
