This file contains the description of labelled data present in annotations.mat

It loads 'annotations' which is a cell of structs. Each struct related to the cars marked in a particular frame sequentially ordered as they appear in the cell.

For each struch, we have the following attributes:
frameId : The image name of the particular frame (string)
carId : The list of cars (N) present in the frame, identified by the sequential id
bbox : A Nx4 matrix that has the bounding box information for each car in the frame, along the row. 
        Bounding box format : [x y width height]
camera : The id of the camera from which the current sequence is taken
