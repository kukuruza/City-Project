% Interface for the Background class
%
% Intended for USERS of the Background class to look up function names
%   Users don't need to see function implementations, only signatures

classdef BackgroundInterface < handle
    methods (Abstract)

         % get foreground mask and optionally denoise it, and merge close
         % parameters:
         %   'denoise', {true, false}
         %   'merge', {true, false}
         mask = step (BS, image, varargin)

    end % methods
end
