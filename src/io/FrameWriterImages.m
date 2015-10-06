% An implementation of FrameWriterInterface for writing frames to a set of images
%   It implements an interface writeNextFrame()
%
% It is essentially a wrapper of vision.VideoWriter
%
% (based on Lynna's createAVI.m code)
%


classdef FrameWriterImages < FrameWriterInterface
    properties (Hidden)
        ext;
        imDir;          % output directory
        counter = 0;
        
        verbose;
    end % properties
    methods
        
        function self = FrameWriterImages (imDir, varargin)
            parser = inputParser;
            addRequired (parser, 'imDir', @ischar);
            addParameter(parser, 'relpath', getenv('CITY_DATA_PATH'), @(x) ischar(x) && exist((x),'dir'));
            addParameter(parser, 'ext', '.jpg', @ischar);
            parse (parser, imDir, varargin{:});
            parsed = parser.Results;

            % make paths relative to input 'relpath'
            imDir = fullfile(parsed.relpath, imDir);

            if ~exist(imDir, 'dir')
                if ~exist(fileparts(imDir), 'dir')
                    error ('FrameWriterImages: parent dir of %s does not exist', imDir);
                end
                mkdir(imDir);
            end
            self.imDir = imDir;
            self.ext = parsed.ext;
        end
        
        function writeNextFrame(self, frame)
            parser = inputParser;
            addRequired(parser, 'frame', @iscolorimage);
            parse (parser, images);

            imPath = fullfile(self.imDir, [sprintf('%06d', self.counter) self.ext]);
            imwrite(frame, imPath);

            self.counter = self.counter + 1;
        end
        
    end % methods
end

