function check = iscolorimage (A)
% checks if the input is a color image
%   function used in inputParser to save space

check = ndims(A) == 3 && size(A,3) == 3 && isa(A, 'uint8');