% class for holding general car info
%

classdef Car
   properties
       bbox  % [x1 y1 width height]
   end % propertioes
   methods
       function C = Car()
       end
       function C = Car (car)
           C.bbox = car.bbox;
       end
   end
end
