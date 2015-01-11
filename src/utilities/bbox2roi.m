function roi = bbox2roi (bbox)

assert (isvector(bbox) && length(bbox) == 4);
assert (all(bbox > 0));

roi = [bbox(2) bbox(1) bbox(4)+bbox(2)-1 bbox(3)+bbox(1)-1];
