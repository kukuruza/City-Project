classdef FasterRcnnDetector < CarDetectorBase
    properties
        
        opts

        model_dir  = fullfile(getenv('FASTERRCNN_ROOT'), 'output/faster_rcnn_final/faster_rcnn_VOC0712_vgg_16layers'); %% VGG-16
        %model_dir  = fullfile(getenv('FASTERRCNN_ROOT'), 'output/faster_rcnn_final/faster_rcnn_VOC0712_ZF'); %% ZF

        rpn_net
        fast_rcnn_net

        proposal_detection_model

        verbose = 0

    end % properties
    methods (Hidden)
        
        function proposal_detection_model = load_proposal_detection_model (~, model_dir)
            ld                          = load(fullfile(model_dir, 'model'));
            proposal_detection_model    = ld.proposal_detection_model;
            clear ld;

            proposal_detection_model.proposal_net_def  = fullfile(model_dir, proposal_detection_model.proposal_net_def);
            proposal_detection_model.proposal_net      = fullfile(model_dir, proposal_detection_model.proposal_net);
            proposal_detection_model.detection_net_def = fullfile(model_dir, proposal_detection_model.detection_net_def);
            proposal_detection_model.detection_net     = fullfile(model_dir, proposal_detection_model.detection_net);
        end

        function aboxes = boxes_filter(~, aboxes, per_nms_topN, nms_overlap_thres, after_nms_topN, use_gpu)
            % to speed up nms
            if per_nms_topN > 0
                aboxes = aboxes(1:min(length(aboxes), per_nms_topN), :);
            end
            % do nms
            if nms_overlap_thres > 0 && nms_overlap_thres < 1
                    aboxes = aboxes(nms(aboxes, nms_overlap_thres, use_gpu), :);       
            end
            if after_nms_topN > 0
                    aboxes = aboxes(1:min(length(aboxes), after_nms_topN), :);
            end
        end

    end
    methods
        
        function self = FasterRcnnDetector (varargin)
            parser = inputParser;
            addParameter(parser, 'use_gpu', true, @islogical);
            parse (parser, varargin{:});
            parsed = parser.Results;

            assert (~isempty(getenv('FASTERRCNN_ROOT')));
            run(fullfile(getenv('FASTERRCNN_ROOT'), 'startup'));

            clear mex;
            clear is_valid_handle; % to clear init_key

            % -------------------- CONFIG --------------------
            self.opts.use_gpu           = parsed.use_gpu;
            self.opts.caffe_version     = 'caffe_faster_rcnn';
            if self.opts.use_gpu
                self.opts.gpu_id        = auto_select_gpu;
                %self.opts.gpu_id        = gpuDevice(1);
                active_caffe_mex(self.opts.gpu_id, self.opts.caffe_version);
            end

            self.opts.per_nms_topN      = 6000;
            self.opts.nms_overlap_thres = 0.7;
            self.opts.after_nms_topN    = 300;
            self.opts.test_scales       = 600;

            % -------------------- INIT_MODEL --------------------
            self.proposal_detection_model    = self.load_proposal_detection_model (self.model_dir);

            self.proposal_detection_model.conf_proposal.test_scales = self.opts.test_scales;
            self.proposal_detection_model.conf_detection.test_scales = self.opts.test_scales;
            if self.opts.use_gpu
                self.proposal_detection_model.conf_proposal.image_means = gpuArray(self.proposal_detection_model.conf_proposal.image_means);
                self.proposal_detection_model.conf_detection.image_means = gpuArray(self.proposal_detection_model.conf_detection.image_means);
            end

            caffe.init_log(fullfile(getenv('CITY_PATH'), 'log/caffe.log'));
            % proposal net
            self.rpn_net = caffe.Net(self.proposal_detection_model.proposal_net_def, 'test');
            self.rpn_net.copy_from(self.proposal_detection_model.proposal_net);
            % fast rcnn net
            self.fast_rcnn_net = caffe.Net(self.proposal_detection_model.detection_net_def, 'test');
            self.fast_rcnn_net.copy_from(self.proposal_detection_model.detection_net);

            % set gpu/cpu
            if self.opts.use_gpu
                caffe.set_mode_gpu();
            else
                caffe.set_mode_cpu();
            end

        end
        
        
        function setVerbosity (self, verbose)
            self.verbose = verbose;
        end

        
        function cars = detect (self, img)
            parser = inputParser;
            addRequired(parser, 'img', @iscolorimage);
            parse (parser, img);
            
            
            if self.opts.use_gpu
                img = gpuArray(img);
            end

            % deploy proposal
            [boxes, scores] = proposal_im_detect(self.proposal_detection_model.conf_proposal, self.rpn_net, img);
            aboxes          = self.boxes_filter([boxes, scores], self.opts.per_nms_topN,   self.opts.nms_overlap_thres, ...
                                                                 self.opts.after_nms_topN, self.opts.use_gpu);

            % deploy detection
            if self.proposal_detection_model.is_share_feature
                [boxes, scores] = fast_rcnn_conv_feat_detect(self.proposal_detection_model.conf_detection, self.fast_rcnn_net, img, ...
                    self.rpn_net.blobs(self.proposal_detection_model.last_shared_output_blob_name), ...
                    aboxes(:, 1:4), self.opts.after_nms_topN);
            else
                [boxes, scores] = fast_rcnn_im_detect(self.proposal_detection_model.conf_detection, self.fast_rcnn_net, img, ...
                    aboxes(:, 1:4), self.opts.after_nms_topN);
            end
            
            classes = self.proposal_detection_model.classes;
            boxes_cell = cell(length(classes), 1);
            thres = 0.6;
            for i = 1:length(boxes_cell)
                boxes_cell{i} = [boxes(:, (1+(i-1)*4):(i*4)), scores(:, i)];
                boxes_cell{i} = boxes_cell{i}(nms(boxes_cell{i}, 0.3), :);

                I = boxes_cell{i}(:, 5) >= thres;
                boxes_cell{i} = boxes_cell{i}(I, :);
            end
            
            if self.verbose > 1
                showboxes(im, boxes_cell, classes, 'voc');
                pause(0.1);
            end
            if self.verbose
                fprintf ('detected %d boxes', length(boxes_cell));
            end
            
            % Faster-RCNN output format to Car objects
            cars = Car.empty;
            for i = 1:length(boxes_cell)
                if isempty(boxes_cell{i})
                    continue;
                end
                for j = 1:size(boxes_cell{i})
                    roiXY = boxes_cell{i}(j, 1:4);
                    box = [roiXY(1), roiXY(2), roiXY(3)-roiXY(1), roiXY(4)-roiXY(2)];
                    name = classes{i};
                    score = boxes_cell{i}(j, end);
                    car = Car('bbox', box, 'name', name, 'score', score);
                    cars = [cars; car];  % naive O(n^2)
                end
            end
        end
       
        function delete(self)
            caffe.reset_all();
            %reset(self.opts.gpu_id);
        end

    end % methods
end
