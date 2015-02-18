function car = pycar2car (pycar)
% pycar2car turns Pycar structure saved in python, to matlab Car

    parser = inputParser;
    addRequired (parser, 'pycar', @isstruct);
    parse (parser, pycar);

    car = Car(pycar.bbox);
    car.patch = pycar.patch;
    car.ghost = pycar.ghost;

    car.orientation = [pycar.yaw, pycar.pitch];
    car.name = pycar.name;
end
