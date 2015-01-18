% Script to select the appropriate camera needed for paper results

clear all; restoredefaultpath

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% Selecting manually input frames
selectedList = [];
for cameraId = 100:1000
    frameReader = GenericFrameReaderInternet (cameraId);
    if(frameReader.checkCameraValidity())
        fprintf('Current camera %d\n', cameraId);
        [frame, timeInterval] = frameReader.getNewFrame();
        
        figure(1); imshow(frame)
        result = input('Press 0 to skip, 1 to record: ');
        if(result)
            selectedList = [selectedList, cameraId];
            fprintf('Current camera %d saved \n', cameraId);
        end
    end
end

% Saving the list
save('selectedCameras.mat', 'selectedList');