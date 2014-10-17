function d=kullback_leibler_divergence(XI,XJ)

  
  m=size(XJ,1); % number of samples of p
  p=size(XI,2); % dimension of samples
  
  assert(p == size(XJ,2)); % equal dimensions
  assert(size(XI,1) == 1); % pdist requires XI to be a single sample
  
  d=zeros(m,1); % initialize output array
  
  for i=1:m
    for j=1:p
      %d(i,1) = d(i,1) + (XJ(i,j) * log(XJ(i,j) / XI(1,j))); % XI is the model!
			if XI(1,j) ~= 0
				d(i,1) = d(i,1) + (XI(1,j) * log(XI(1,j) / XJ(i,j))); % XJ is the model! makes it possible to determine each "likelihood" that XI was drawn from each of the models in XJ
			end
    end
  end
