function F = soapFilm (F, hard, varargin)
    parser = inputParser;
    addRequired(parser, 'F', @ismatrix);
    addRequired(parser, 'mask', @(x) islogical(x) && ismatrix(x));
    addParameter(parser, 'ignore', [], @(x) ismatrix(x) && islogical(x));
    addParameter(parser, 'Size', 1, @isscalar);
    addParameter(parser, 'MaxNumIter', 10000, @isscalar);
    addParameter(parser, 'Thresh', 0.1, @isscalar);
    addParameter(parser, 'video', []);
    addParameter(parser, 'verbose', 0, @isscalar);
    parse (parser, F, hard, varargin{:});
    
    parsed = parser.Results;
    sz = parsed.Size;
    F = parsed.F;
    hard = parsed.mask;
    ignore = parsed.ignore;
    if isempty(ignore), ignore = false(size(hard)); end

    if parsed.verbose > 2
        imagesc(hard);
        waitforbuttonpress
        imagesc(ignore);
        waitforbuttonpress
        imagesc(~hard & ~ignore);
        waitforbuttonpress
    end

    se = fspecial('average', sz * 2 + 1);
    
    F = padarray (F, [sz sz]);
    hard = padarray (hard, [sz sz]);
    ignore = padarray (ignore, [sz sz], true);

    F0 = F;
    for it = 1 : parsed.MaxNumIter
        F1 = F;
        
        % average
        F = imfilter (F, se, 'replicate');
        ignore_filt = imfilter (double(~ignore), se, 'replicate');
        
        % adjust for ignore
        F = F ./ ignore_filt;
        F(isnan(F)) = 0;
        F(ignore) = 0;
        
        % reset hard constraints
        F(hard) = F0(hard);

        if parsed.verbose > 0
            imagesc(F);
            pause (0.1)
        end
        if ~isempty(parsed.video)
            writeVideo (parsed.video, getframe);
        end
        
        % exit condition on threshold
        dF = F - F1;
        delta = sum(abs(dF(~ignore))) / double(numel(dF(~ignore)));
        if parsed.verbose > 0
            fprintf ('iter: %d, delta: %f\n', it, delta);
        end
        if delta < parsed.Thresh, break, end
    end
    
    F = F (sz+1 : size(F,1)-sz, sz+1 : size(F,2)-sz);
end
