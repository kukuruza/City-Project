function im = drawRect(im, bb, color)
%DRAWRECT draw rectagle from the bounding box bb = [x1 y1 width height]

    assert (ismatrix(im) || (ndims(im) == 3 && size(im,3) == 3));
    assert (isvector(bb) && length(bb) == 4);
    assert (bb(1) >= 1 && bb(1)+bb(3) < size(im,2));
    assert (bb(2) >= 1 && bb(2)+bb(4) < size(im,1));

    if ismatrix(im); nCh = 1; else nCh = 3; end
    for c = 1 : nCh
        im (bb(2) : bb(2)+bb(4)-1, bb(1), c)         = color(c);
        im (bb(2) : bb(2)+bb(4)-1, bb(1)+bb(3)-1, c) = color(c);
        im (bb(2), bb(1) : bb(1)+bb(3)-1, c)         = color(c);
        im (bb(2)+bb(4)-1, bb(1) : bb(1)+bb(3)-1, c) = color(c);
    end
end