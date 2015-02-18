function pycarsDir2carsDir (dir_in, dir_out)
% PycarsDir2carsDir rewrites pycars in a dir as matlab Cars

parser = inputParser;
addRequired (parser, 'dir_in', @(x) ischar(x) && exist(dir_in, 'dir'));
addRequired (parser, 'dir_out', @ischar);
parse (parser, dir_in, dir_out);

pycars_path_list = dir (fullfile(dir_in, '*.mat'));

if ~exist(dir_out, 'dir')
    mkdir (dir_out)
end

for i = 1 : length(pycars_path_list)
    
    % read pycars
    pycars_path = fullfile(dir_in, pycars_path_list(i).name);
    load (pycars_path)
    pycars = cars;
    clear cars
    
    % make cars from pycars
    cars = Car.empty;
    for j = 1 : length(pycars)
        cars(j) = pycar.pycar2car(pycars{j});
    end
    
    % save cars
    cars_path = fullfile(dir_out, pycars_path_list(i).name);
    save (cars_path, 'cars');

end
