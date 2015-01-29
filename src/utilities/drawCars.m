function img = drawCars (img, cars, varargin)
%DRAWCARS draw cars in the image
%
% Input:
%     img
%     cars
% Parameters: 
%     all input parameters are passed to Car.drawCar()
%

parser = inputParser;
addRequired (parser, 'img', @iscolorimage);
addRequired (parser, 'cars', @(x) isa(x, 'Car') && isvector(cars));
parse (parser, img, cars);

for i = 1 : length(cars)
    img = cars(i).drawCar(img, varargin{:});
end
