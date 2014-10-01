% class for holding general car info
%

classdef CarAppearance < Car
    properties
        iFrame;
        feature;
    end
    methods
        function C = CarAppearance (car, iFrame)
            C = C@Car(); % FIXME: superclass from subclass
            C.iFrame = iFrame;
        end
        function generateFeature (C, image, imagemask)
            roi = [C.bbox(2) C.bbox(1) C.bbox(4)+C.bbox(2)-1 C.bbox(3)+C.bbox(1)-1];
            patch  = image(roi);       % color patch from the image the samesize as bbox
            mask = imagemask (roi);        % bw mask for the car in the patch
            % logic
            C.feature = [];
        end
    end % methods
end