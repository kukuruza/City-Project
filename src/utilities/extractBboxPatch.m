function patch = extractBboxPatch (img, bbox)
%extractBbox - extracts patch described by an bbox from image

assert (isvector(bbox) && length(bbox) == 4);
roi = [bbox(1), bbox(2), bbox(1)+bbox(3)-1, bbox(2)+bbox(4)-1];
patch = img (roi(2) : roi(4), roi(1) : roi(3), :);