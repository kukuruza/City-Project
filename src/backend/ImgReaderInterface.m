classdef ImgReaderInterface < handle
    % The backend for reading images from dataset
    % Diffrent implementations depending on how images are stored.
    %   Examples of storage is folder with images or video.
    
    methods (Abstract)
        imread (self, image_id)
        
        maskread (self, mask_id)
    end
end
