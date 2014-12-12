%Function to compute the homography between two images obtained by solving the homography equations using corresponding points
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%5
%
%Inputs : (p1, p2) - Corresponding arrays of points with each 2 x N
%Outputs : H2to1 - 3 x 3 is the homography from image 2 to image 1
%Usage: homo2to1 = computeH(pts1, pts2)
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%5
function[H2to1] = computeH(p1, p2)
    %Getting the constraints to the form Ah = 0, to apply Rayleigh Quotient method for solving the least square system

    A = [];
    %Error checking for incompatible sizes
    if(size(p1, 1) ~= 2 || size(p2,1) ~= 2 || size(p1, 2) ~= size(p2, 2))
        fprintf('Incompatible sizes of p1, p2 in computeH\n');
        return
    end

    %Looping over all the point pairs available for homography computation
    %to gather constraints for solving Ah = 0
    for i = 1 : size(p1, 2)
        A = [A ; 
            p2(1, i), p2(2, i), 1, 0, 0, 0, -p1(1,i)*p2(1,i), -p1(1,i)*p2(2,i), -p1(1,i);
            0, 0, 0, p2(1, i), p2(2, i), 1, -p1(2,i)*p2(1,i), -p1(2,i)*p2(2,i), -p1(2,i)];
    end

    %Finding the eigenvector of the least eigenvalue which is the minimizer according to Rayleigh Theorem 
    [V, D] = eig(A'*A);
    %homoVec = V(:,1);
    %H2to1 = [homoVec(1:3), homoVec(4:6), homoVec(7:9)];
    H2to1 = [V(1:3, 1), V(4:6, 1), V(7:9, 1)]';
end
