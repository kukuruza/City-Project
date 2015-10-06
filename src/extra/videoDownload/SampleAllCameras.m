function sampleAllCameras (dirpath)
% collect images from every camera

% set paths
assert (~isempty(getenv('CITY_DATA_PATH')));  % make sure environm. var set
CITY_DATA_PATH = [getenv('CITY_DATA_PATH') '/'];    % make a local copy
addpath(genpath(fullfile(getenv('CITY_PATH'), 'src')));  % add tree to search path

% file for output
fout = fopen ([dirpath 'out.txt'], 'w');

% file for titles
ftitles = fopen ([dirpath, 'readme.txt'], 'w');

verbose = 1;


urlViewerPart = 'http://nyctmc.org/google_popup.php?cid=';
% url example: http://207.251.86.238/cctv360.jpg?rand=0988954345345
urlPart1 = 'http://207.251.86.238/cctv';
urlPart2 = '.jpg?rand=';

for camNum = 100 : 999
    
    fprintf ('%d\n', camNum);
    
    % open the viewer and read the html
    urlViewer = [urlViewerPart num2str(camNum)];
    content = urlread(urlViewer);

    % find the camera number in the html
    id = regexp(content, 'http://207.251.86.238/cctv\d+', 'match');
    title = regexp(content, 'title\>.*\</title', 'match');

    if isempty(id)
        fprintf (fout, '%d empty id \n', camNum);
        continue
    end

    % set the camera number and image url
    idStr = id{1}(27:end);
    url = [urlPart1 num2str(idStr) urlPart2];

    % get image
    try
        image = imread([url num2str(now)]);
    catch
        fprintf (fout, '%d failed to read\n', camNum);
        continue
    end

    % when a camera is serviced, image is grayscale
    if ismatrix(image)
        fprintf (fout, '%d service\n', camNum);
        continue
    end
    
    % if not video, image is mostly black
    NoVideoThresh = 25;
    if mean(image(:)) < NoVideoThresh
        fprintf (fout, '%d no video\n', camNum);
        continue
    end
    
    % save image
    impath = [dirpath num2str(camNum) '.jpg'];
    imwrite (image, impath);
    if verbose, imshow(image), pause(0.1); end
    
    % save title
    if isempty(title)
        fprintf (fout, '%d suceeded, no title\n', camNum);
    else
        fprintf (ftitles, '%d: %s\n', camNum, title{1}(7:end-7));
        fprintf (fout, '%d suceeded\n', camNum);
    end
    
end

fclose (ftitles);
fclose (fout);
