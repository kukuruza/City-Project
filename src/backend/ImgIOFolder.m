classdef ImgIOFolder < ImgReaderInterface & ImgWriterInterface
    % Implementation of both reading and writing in a dataset
    %   based on storing imagefiles as .jpg (images) and .png (masks)
    
    properties
        relpath = '.';
        verbose = 0;
        
        image_cache
        mask_cache
    end
    methods
        
        function self = ImgIOFolder (varargin)
            % 'verbose' -- level of output verbosity
            % 'relpath' -- relative path in all further functions
            parser = inputParser;
            addParameter(parser, 'verbose', 0, @isscalar);
            addParameter(parser, 'relpath', getenv('CITY_DATA_PATH'), @ischar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            self.relpath = parsed.relpath;
            self.verbose = parsed.verbose;
            
            self.image_cache = containers.Map('KeyType','char','ValueType','uint8');
            self.mask_cache  = containers.Map('KeyType','char','ValueType','uint8');
        end
        
        function img = readImpl (self, id)
            imagepath = fullfile(self.relpath, id);
            if exist(imagepath, 'file') == 0
                error (sprintf('imagepath does not exist: %s', imagepath));
            end
            img = imread(imagepath);
        end
        
        function writeImpl (self, img, id)
            imagepath = fullfile(self.relpath, id);
            imagedir = fileparts(imagepath);
            if exist(imagedir, 'file') == 0
                mkdir (imagedir);  % TODO: whole tree, not just parent dir
            end
            imwrite(img, imagepath);
        end
        
        function image = imread (self, image_id)
            % see if the value is in cache
            if isKey(self.image_cache, image_id)
                if self.verbose > 1, fprintf('imread: found image in cache.\n'); end
                image = self.image_cache(image_id);
            else
                image = self.readImpl(image_id);
                if self.verbose > 1, fprintf('imread: updating cache with "%s".\n', image_id); end
                self.image_cache = containers.Map(image_id, image);
            end
        end
        
        function mask = maskread (self, mask_id)
            % see if the value is in cache
            if isKey(self.mask_cache, mask_id)
                if self.verbose > 1, fprintf('maskread: found mask in cache.\n'); end
                mask = self.mask_cache(mask_id);
            else
                mask = self.readImpl(mask_id);
                if self.verbose > 1, fprintf('maskread: updating cache.\n'); end
                self.mask_cache = containers.Map(mask_id, mask);
            end
        end
        
        function imwrite (self, image, image_id)
            assert (iscolorimage(image));
            self.writeImpl (image, image_id);
        end

        function maskwrite (self, mask, mask_id)
            assert (ismatrix(mask));
            self.writeImpl (mask, mask_id);
        end

        function close (~)
        end
    end
end