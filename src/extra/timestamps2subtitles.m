function timestamps2subtitles (timestamps_path, srt_path, framerate)

% read the times file as a matrix
times = dlmread(timestamps_path);
assert (size(times,2) == 6);

% write srt file
fid = fopen(srt_path, 'w');
t0 = times(1,:);
t1 = t0;
% starting with second frame to the end
for i = 2 : size(times,1)
    t2 = times(i,:);

    e1 = i-2;                % elapsed since start of movie
    e1 = e1 / framerate;            % adjust for the frame 
    ss1 = mod(e1, 60);       % seconds with decimal part
    ms1 = ss1 - floor(ss1);  % ms
    ss1 = floor(ss1);        % integer seconds
    e1 = floor(e1 / 60);     % minutes and hours together
    mm1 = mod(e1, 60);       % minutes
    hh1 = floor(e1 / 60);    % hours
    
    e2 = i-1;
    e2 = e2 / framerate;
    ss2 = mod(e2, 60);
    ms2 = ss2 - floor(ss2);
    ss2 = floor(ss2);
    e2 = floor(e2 / 60);
    mm2 = mod(e2, 60);
    hh2 = floor(e2 / 60);
    
    fprintf (fid, '%d\n', i-1);
    fprintf (fid, '%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n', ...
        hh1, mm1, ss1, floor(ms1 * 1000), hh2, mm2, ss2, floor(ms2 * 1000));
    fprintf (fid, '%f sec.\n', etime(t2, t1));
    fprintf (fid, '\n');
    t1 = t2;
end
fclose(fid);
    