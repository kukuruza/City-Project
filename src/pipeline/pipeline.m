% pipeline
%

im0 = imread('somewhere');

backSubtractor = BackgroundSubtractor(im0);

geom = GeometryEstimator(im0);



i = 0;
while 1
    
    name = 'get some name(i)';
    
    im = imread(name);
    gray = rgb2gray(im);
    
    % subtract backgroubd and return mask
    foregroundMask = backSubtractor.subtract(im);
    
    % morphological operation with foreground mask
    
    % geometry should process the mask
    [ROIs, scales, orientation] = geom.guess(foregroundMask);
    assert(size(ROIs,1) == 4);
    assert(isvector(scale));
    %assert(orientation makes sense)
    assert(size(ROIs,2) == length(scales) && size(ROIs,2) == length(orientations));
    N = size(ROIs,2);
    
    % actually detect cars
    cars = cell(1,N);
    for iPatch = 1 : N
        roi = ROIs(j);
        patch;% = gray %%%
        cars(j) =  detectCar(patch, scales(j), orientations(j));
    end
    
    % HMM processing
    
    % counting
    
end
