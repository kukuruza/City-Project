function[displayOrientImg] = displayOrientationImage(orientationMap, grayImage)
    % Function to dump the orientation map, after rescaling showing the
    % orientation of the best response of filter, returns the image to be 
    % dumped
    %
    % Usage:
    % displayOrientImg = displayOrientationImage(orientationMap, grayImage)

    %%%%%%%%%%%%%%% show the orientation bar on resized image %%%%%%%%%%%%%%%%%%%%%%%
    resizedOrientImg = imresize(orientationMap, 2, 'bilinear');
    displayOrientImg = imresize(grayImage(:, :, [1 1 1]), 2, 'bilinear');
    [imageH, imageW] = size(grayImage);

    barLen = 4;
    barWid = 1;
    for i=10:8:imageH*2-10
        for j=10:8:imageW*2-10
            ori = resizedOrientImg(i,j); 
            if (ori==90)
                yy = i;
                xx = j;
                displayOrientImg(yy:yy+barLen,xx-barWid:xx,1) = 255;
                displayOrientImg(yy:yy+barLen,xx-barWid:xx,2) = 0;
                displayOrientImg(yy:yy+barLen,xx-barWid:xx,3) = 0;
            elseif (ori==180)||(ori==0)
                displayOrientImg(i-barWid:i,j:j+barLen,1) = 255;
                displayOrientImg(i-barWid:i,j:j+barLen,2) = 0;
                displayOrientImg(i-barWid:i,j:j+barLen,3) = 0;
            else
                if (ori<=45)||(ori>=135)
                    kk = tan(ori*pi/180);
                    for xx=j:j+barLen
                        yy = round(kk*(xx-j) + i);
                        if (yy>=i-barLen)&&(yy<=i+barLen) 
                            displayOrientImg(yy,xx-barWid:xx,1) = 255;
                            displayOrientImg(yy,xx-barWid:xx,2) = 0;
                            displayOrientImg(yy,xx-barWid:xx,3) = 0;
                        end
                    end
                elseif (ori>45)&&(ori<135)
                    kk = tan(ori*pi/180);
                    for yy=i:i+barLen
                        xx = round((yy-i)/kk + j);
                        if (xx>=j-barLen)&&(xx<=j+barLen) 
                            displayOrientImg(yy-barWid:yy,xx,1) = 255;
                            displayOrientImg(yy-barWid:yy,xx,2) = 0;
                            displayOrientImg(yy-barWid:yy,xx,3) = 0;
                        end
                    end
                end
            end
        end
    end
end
