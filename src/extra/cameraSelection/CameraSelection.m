% Script to select the appropriate camera needed for paper results

clear all; %restoredefaultpath

% setup all the paths
run ../../rootPathsSetup.m;
run ../../subdirPathsSetup.m;

% change dir to the directory of this script
cd (fileparts(mfilename('fullpath')));

% Selecting manually input frames
%selectedList = [];
%load('selectedCameras.mat')

seriesSpan = false;
if(seriesSpan)
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
end

dumpFrames = false;
if(dumpFrames)
    nFrames = 30;
    % Reading each of the selected cameras and dumping their files here
    finalList = [];
    for i = 21:length(selectedList)
        cameraId = selectedList(i);
        imagePath = [CITY_DATA_PATH '2-min/camdata/cam', num2str(cameraId), '/'];

        % Creating the folder if it doesnt exists
        if(~exist(imagePath, 'dir'))
            mkdir(imagePath)
        end

        frameReader = FrameReaderInternet(cameraId);
        images = cell(1, nFrames);
        fprintf('Current camera %d\n', cameraId);

        % Getting first nFrames
        for j = 1:nFrames
            fprintf('Saving frame (%d / %d) for camera %d (%d / %d) \n',...
                j, nFrames, cameraId, i, length(selectedList));
            imageName = fullfile(imagePath, sprintf('image%04d.png', j));
            [frame, timeInterval] = frameReader.getNewFrame();
            imwrite(frame, imageName, 'png');
            %figure(1); imshow(frame)
        end

        %result = input('Press 0 to skip, 1 to record: ');
        %if(result)
        %    selectedList = [selectedList, cameraId];
        %    fprintf('Current camera %d saved \n', cameraId);
        %end
        %pause()

        %for j = 1:nFrames
            %[frame, timeInterval] = frameReader.getNewFrame();
            %images{j} = frame;


        %end
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Generating the entire geometry initialization
%who