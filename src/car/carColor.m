function color = carColor( car )
%extractCarColor extract the color of an object of class Car as RGB
%   This is a dummy. Shanghang is working on the content


% validate input
parser = inputParser;
addRequired(parser, 'car', @(x) isa(x, 'Car') || isscalar(x));
parse (parser, car);



% useful code goes here



% this is a dummy result
color = [1 0 0];

end

