function d=match_distance(XI,XJ)
  % Implementation of the match distance to use with pdist
  
  m=size(XJ,1); % number of samples of p
  p=size(XI,2); % dimension of samples
  
  assert(p == size(XJ,2)); % equal dimensions
  assert(size(XI,1) == 1); % pdist requires XI to be a single sample
  
  d=zeros(m,1); % initialize output array
  
  cxi=cumsum(XI,2); % cumulative histograms
  cxj=cumsum(XJ,2); % cumulative histograms
  
  for i=1:m
    for j=1:p
      d(i,1) = d(i,1) + abs(cxi(1,j) - cxj(i,j));
    end
  end
