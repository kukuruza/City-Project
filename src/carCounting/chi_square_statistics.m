function d=chi_square_statistics(XI,XJ)
  % Implementation of the Chi^2 distance to use with pdist
  
  m=size(XJ,1); % number of samples of p
  p=size(XI,2); % dimension of samples
  
  assert(p == size(XJ,2)); % equal dimensions
  assert(size(XI,1) == 1); % pdist requires XI to be a single sample
  
  d=zeros(m,1); % initialize output array
  
  for i=1:m
    for j=1:p
      m=(XI(1,j) + XJ(i,j)) / 2;
			if m ~= 0 % if m == 0, then xi and xj are both 0 ... this way we avoid the problem with (xj - m)^2 / m = (0 - 0)^2 / 0 = 0 / 0 = ?
				d(i,1) = d(i,1) + ((XI(1,j) - m)^2 / m); % XJ is the model! makes it possible to determine each "likelihood" that XI was drawn from each of the models in XJ
			end
    end
  end