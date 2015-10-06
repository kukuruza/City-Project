classdef ImgDbWriterInterface < handle
    % The backend for writing images to a new [or existing] dataset
    % Different implementations depending on how images are stored.
    %   Examples of storage is folder with images or video.
    
    methods (Abstract)
        imwrite (self, image, image_id)   % for RGB image
        
        maskwrite (self, mask, mask_id)   % for binary grayscale mask
    end
end
