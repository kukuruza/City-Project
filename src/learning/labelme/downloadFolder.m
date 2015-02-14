
% demo of downloading and processing detections

folder = 'cam572-5pm-pairs';



REMOTE_IMAGES = 'http://mouragroup.org/Images';
REMOTE_ANNOTATIONS = 'http://mouragroup.org/Annotations';

fulldatabase = LMdatabase(REMOTE_ANNOTATIONS);

% make a query for a folder
[D,j] = LMquery(fulldatabase, 'folder', folder, 'exact');

HOME_IMAGES = '/Users/evg/projects/City-Project/data/labelme/Images';
HOME_ANNOTATIONS = '/Users/evg/projects/City-Project/data/labelme/Annotations';
HOME_CARS = '/Users/evg/projects/City-Project/data/labelme/Cars';



LMinstall_parser (HOME_IMAGES, HOME_ANNOTATIONS, 'D', D, 'webpageimg', REMOTE_IMAGES, 'webpageanno', REMOTE_ANNOTATIONS);

