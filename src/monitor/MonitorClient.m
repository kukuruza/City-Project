classdef MonitorClient < handle
    properties (Hidden)
        
        enabled;    % false, if disabled
        
        server_url;
        
        machine_name;
        cam_id;
        cam_timezone;
        frame_num = 0;
        
        verbose;
        
    end
    methods
        
        function self = MonitorClient(varargin)
            % 'verbose' -- level of output verbosity
            % 'relpath' -- relative path in all further functions for tests
            parser = inputParser;
            addParameter(parser, 'cam_id', [], @isscalar);      % required
            addParameter(parser, 'config_path', [], @ischar);   % required
            addParameter(parser, 'cam_timezone', 'America/New_York', @isscalar);
            addParameter(parser, 'relpath', getenv('CITY_PATH'), @ischar);
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            % read config file
            config_path = fullfile(parsed.relpath, parsed.config_path);
            if ~exist(config_path, 'file')
                error ('config file does not exist: "%s"\n', config_path);
            end
            readKeys = {'monitor','','enable','i';...
                        'monitor','','server_url','';...
                        'monitor','','machine_name',''};
            readSett = inifile(config_path, 'read', readKeys);
            self.enabled      = readSett{1} ~= 0;
            self.server_url   = readSett{2};
            self.machine_name = readSett{3};
            
            % other parameters
            self.cam_id = parsed.cam_id;
            self.cam_timezone = parsed.cam_timezone;
            self.verbose = parsed.verbose;
            
            if self.verbose
                fprintf ('MonitorClient constructed with:\n');
                fprintf ('  enabled:      %d\n', int32(self.enabled));
                fprintf ('  server_url:   %s\n', self.server_url);
                fprintf ('  machine_name: %s\n', self.machine_name);
            end
        end
        
        function success = updateDownload(self)
            
            % update frame
            self.frame_num = self.frame_num + 1;
            
            % get time where the computer is located
            %machine_time = datestr(datetime());
            
            % get name of the program which called me
            s = dbstack;
            program_name = s(2).file;
            
            % form json
            json_struct = struct('machine_name', self.machine_name, ...
                                 'program_name', program_name, ...
                                 'camera_id',    self.cam_id, ...
                                 'camera_time_zone', self.cam_timezone, ...
                                 'frame_num',    self.frame_num);
            json = savejson('',json_struct);
            if self.verbose > 1, json, end
            
            % for some reason matlab does not understand success response
            % wrap around try-catch as a workaround
            tic
            try
                % send a POST HTTP request
                % elasticsearch index name: "download"
                % elasticsearch type:       "status_update"
                options = weboptions('Timeout', 1);
                webwrite([self.server_url, '/download/status_update'], json, options);
            catch
                ;
            end
            toc
            success = 1;
        end
        
    end
end