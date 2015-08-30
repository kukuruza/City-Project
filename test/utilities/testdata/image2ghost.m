function ghost = image2ghost (image, backimage)
    assert (all(size(image) == size(backimage)));
    ghost = uint8(int32(image) - int32(backimage) + 128);
end