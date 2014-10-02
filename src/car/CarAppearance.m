% class for holding general car info
%

classdef CarAppearance < Car
    properties (Hidden)
        iFrame;
        feature = [];
    end
    methods
        function C = CarAppearance (car, iFrame)
            C = C@Car(car.bbox);
            C.iFrame = iFrame;
        end
        function generateFeature (C, image, imagemask)
            roi = C.getROI();          % a method of Car
            patch  = image(roi);       % color patch from the image the samesize as bbox
            mask = imagemask (roi);    % bw mask for the car in the patch
            % logic
            C.feature = [];  % TODO: implement
        end
    end % methods
end