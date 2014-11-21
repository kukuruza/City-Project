function transition = matches2transition (matches, N1, N2)
%MATCHES2TRANSITION transforms matches array into transition matrix format
% N1 and N2:      number of cars in the 1st and 2nd images
% transition:     binary matrix N2 x N1, 1 stands for a valid match
% matches array:  K x [num1 num2], 
%   where num1 - car# in the 1st image, num2 - car# in the 2nd image,
%   and K - number of valid matches
%

transition = zeros(N2, N1);

for k = 1 : size(matches,1)
    assert (matches(k,1) <= N1);
    assert (matches(k,2) <= N2);
    transition(matches(k,2), matches(k,1)) = 1;
end
