% An implementation of FrameReaderInterface for reading .jpg images from a dir
%   It implements an interface getNewFrame()
%
% It is essentially a thin wrapper of imread()

classdef FrameReaderImages < FrameReaderInterface
    properties (Hidden)
        imNames;
        imDir;
        counter;
    end % properties
    
    methods
        function self = FrameReaderImages (imDir, varargin)
            parser = inputParser;
            addRequired (parser, 'imDir', @ischar);
            addParameter(parser, 'relpath', getenv('CITY_DATA_PATH'), @(x) ischar(x) && exist((x),'dir'));
            addParameter(parser, 'ext', '.jpg', @ischar);
            parse (parser, imDir, varargin{:});
            parsed = parser.Results;

            % make paths relative to input 'relpath'
            imDir = fullfile(parsed.relpath, imDir);

            self.imDir = imDir;
            imTemplate = fullfile(self.imDir, ['*' parsed.ext]);
            self.imNames = dir (imTemplate);
            self.counter = 1;
            
            if ~exist(self.imDir, 'dir')
                error('FrameReaderImages(): imDir %s does not exist', imDir);
            end
            
            if isempty(self.imNames)
                error('FrameReaderImages(): imNames is empty for template %s', imTemplate);
            end
        end
        function [frame, timestamp] = getNewFrame(self)
            if self.counter > length(self.imNames)
                frame = [];
            else
                frame = imread(fullfile(self.imDir, self.imNames(self.counter).name));
            end
            self.counter = self.counter + 1;
            timestamp = '';
        end
    end % methods
    
end

