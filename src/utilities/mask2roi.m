function roi = mask2roi (mask)

assert (ismatrix(mask));
assert (islogical(mask));

% empty mask
if nnz(mask) == 0, roi = []; return, end

% init
roi(1) = size(mask,1);
roi(2) = size(mask,2);
roi(3) = 1;
roi(4) = 1;

% row by row
for y = 1 : size(mask,1)
    if nnz(mask(y,:)) == 0, continue, end
    
    ind = find(mask(y,:), 1, 'first');
    if ind < roi(2), roi(2) = ind; end
    
    ind = find(mask(y,:), 1, 'last');
    if ind > roi(4), roi(4) = ind; end
end

% col by col
for x = 1 : size(mask,2)
    if nnz(mask(:,x)) == 0, continue, end
    
    ind = find(mask(:,x), 1, 'first');
    if ind < roi(1), roi(1) = ind; end
    
    ind = find(mask(:,x), 1, 'last');
    if ind > roi(3), roi(3) = ind; end
end
