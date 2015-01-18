function darkghost = gray2darkghost (grayghost)
% transform gray background of ghosts of cars to dark background
%   a simple helper function to reduce code and eliminate errors
%   warning: information is got lost, function is not invertible

parser = inputParser;
addRequired(parser, 'grayghost', @iscolorimage);
parse (parser, grayghost);

darkghost = uint8(abs(int32(grayghost) - 128));
