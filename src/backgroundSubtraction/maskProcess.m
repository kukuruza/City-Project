function maskOut = maskProcess (fgMask)


[h,w]=size(fgMask);
Th = 0.00005*h*w;

% imshow(fgMask);

L = bwlabel(fgMask,8);
for j = 1:max(L(1:end))
    [r,c]=find(L==j);
    if length(r)<Th
        L(r,c)=0;
    end
end

[y,x] = find(L~=0);
if length(y)~=0
k = convhull(x,y);
% figure();
% plot(x(k),y(k),'r-',x,y,'b*')

[X0,Y0]=meshgrid(1:w,1:h);
X = X0(:)';%resize(X0,~,1);
Y = Y0(:)';%resize(Y0,~,1);

[in,on] = inpolygon(Y,X,y(k),x(k));
% figure();
% plot(x(k),y(k)) % polygon
% axis equal

% hold on
% plot(X(in),Y(in),'r+') % points inside
% plot(X(~in),Y(~in),'bo') % points outside
% hold off

% figure();
maskOut = fgMask;
maskOut(in)=1;
maskOut(~in)=0;
else
    maskOut = fgMask;
end
% imshow(maskOut);