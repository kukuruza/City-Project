function ghost = patch2ghost (patch, background)
% make a gray ghost from patch
ghost = uint8((int32(patch) - int32(background)) / 2 + 128);