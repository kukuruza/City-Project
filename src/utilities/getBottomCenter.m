function center = getBottomCenter (bbox) % [y x]
    HeightRatio = 0.75;
    center = [int32(bbox(2) + bbox(4) * HeightRatio - 1), ...
              int32(bbox(1) + bbox(3) / 2)];  % why is it -1 ???
end
