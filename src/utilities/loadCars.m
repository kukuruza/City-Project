function cars = loadCars (carsDir, varargin)
%LOADCARS load car objects into a list
% Objects are loaded from carsDir, each object is stored in a mat file
%   that matches carsNameTemplate.
%
% Parameters:
%   'nameTemplate', '*.mat'

parser = inputParser;
addRequired(parser, 'carsDir', @(x) exist(x, 'dir'));
addParameter(parser, 'nameTemplate', '*.mat', @ischar);
parse (parser, carsDir, varargin{:});
parsed = parser.Results;


carList = dir(fullfile(carsDir, parsed.nameTemplate));

cars = Car.empty();

% load detections
for i = 1 : length(carList)
    clear car;

    carPath = fullfile(carsDir, carList(i).name);
    load (carPath);
    
    cars = [cars; car];
end
    
