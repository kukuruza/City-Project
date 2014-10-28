
% input txt file
inTimesPath = '/Users/evg/projects/City-Project/data/camdata/cam572/5-hours-dusk/uncut.txt';
outSrtPath = '/Users/evg/projects/City-Project/data/camdata/cam572/5-hours-dusk/uncut.srt';

% read the times file as a matrix
times = dlmread(inTimesPath);
assert (size(times,2) == 6);

% write srt file
fid = fopen(outSrtPath, 'w');
t0 = times(1,:);
t1 = t0;
for i = 1 : size(times,1)
    t2 = times(i,:);
    
    fprintf (fid, '%d\n', i);
    fprintf (fid, '%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n');
    fprintf (fid, '%f sec.\n', etime(t2, t1));
    fprintf (fid, '\n');
    t1 = t2;
end
fclose(fid);
    