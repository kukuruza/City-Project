% demo of downloading and processing detections

folder = 'cam572-bright-frames';



REMOTE_IMAGES = 'http://mouragroup.org/Images';
REMOTE_ANNOTATIONS = 'http://mouragroup.org/Annotations';

fulldatabase = LMdatabase(REMOTE_ANNOTATIONS);

%  
[D,j] = LMquery(fulldatabase, 'folder', folder, 'exact');
LMdbshowscenes(fulldatabase(j), REMOTE_IMAGES); % this shows all the objects


