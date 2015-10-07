function UoI = getUoI (roi1, roi2)

y1i = max(roi1(1), roi2(1));
x1i = max(roi1(2), roi2(2));
y2i = min(roi1(3), roi2(3));
x2i = min(roi1(4), roi2(4));

if x1i >= x2i || y1i >= y2i
    inters = 0;
else
    inters = (x2i-x1i)*(y2i-y1i);
end

area1 = (roi1(3)-roi1(1))*(roi1(4)-roi1(2));
area2 = (roi2(3)-roi2(1))*(roi2(4)-roi2(2));
union = area1 + area2 - inters;

UoI = single(inters) / union;
assert (UoI >= 0 && UoI <= 1);
