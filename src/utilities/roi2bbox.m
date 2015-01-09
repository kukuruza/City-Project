function bbox = roi2bbox (roi)

assert (isvector(roi) && length(roi) == 4);
assert (roi(3) >= roi(1) && roi(4) >= roi(2));

bbox = [roi(2) roi(1) roi(4)-roi(2)+1 roi(3)-roi(1)+1];
