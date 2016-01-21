classdef MonitorDownloadClient < handle
    properties (Hidden)
        
        enabled;    % false, if disabled
        
        server_address;
        server_credentials;
        
        machine_name;
        cam_id;
        cam_timezone;
        max_time;      % maximum operation time for curl, sec (string)
        frame_num = 0;
        
        verbose;
        
    end
    methods
        
        function self = MonitorDownloadClient(varargin)
            % 'verbose' -- level of output verbosity
            % 'relpath' -- relative path in all further functions for tests
            parser = inputParser;
            addParameter(parser, 'cam_id', [], @isscalar);      % required
            addParameter(parser, 'config_path', [], @ischar);   % required
            addParameter(parser, 'cam_timezone', '-05:00', @ischar);
            addParameter(parser, 'relpath', getenv('CITY_PATH'), @ischar);
            addParameter(parser, 'verbose', 0, @isscalar);
            parse (parser, varargin{:});
            parsed = parser.Results;
            
            % read config file
            config_path = fullfile(parsed.relpath, parsed.config_path);
            if ~exist(config_path, 'file')
                warning ('MonitorClient(): config file does not exist: "%s"\n', config_path);
                warning ('  will not send data to monitor server.');
                self.enabled = false;
                return
            end
            readKeys = {'download','','enable','i';...
                        'download','','server_address','s';...
                        'download','','server_credentials','s';...
                        'download','','machine_name','s';...
                        'download','','max_time','s'};
            readSett = inifile(config_path, 'read', readKeys);
            self.enabled            = readSett{1} == 1;
            self.server_address     = readSett{2};
            self.server_credentials = readSett{3};
            self.machine_name       = readSett{4};
            self.max_time           = readSett{5};
            
            % other parameters
            self.cam_id = parsed.cam_id;
            self.cam_timezone = parsed.cam_timezone;
            self.verbose = parsed.verbose;
            
            if self.verbose
                fprintf ('MonitorClient constructed with:\n');
                fprintf ('  enabled:            %d\n', int32(self.enabled));
                fprintf ('  server_address:     %s\n', self.server_address);
                fprintf ('  server_credentials: %s\n', self.server_credentials);
                fprintf ('  machine_name:       %s\n', self.machine_name);
                fprintf ('  max_time:           %s\n', self.max_time);
            end
        end
        
        function success = updateDownload(self, timestamp)
            assert (ischar(timestamp));
            
            % update frame
            self.frame_num = self.frame_num + 1;
            
            % stop if not enabled
            if ~self.enabled, 
                success = true; 
                if self.verbose, fprintf ('MonitorDownload is disabled.\n'); end
                return; 
            end
            
            % get name of the program which called me
            s = dbstack;
            program_name = s(2).file;
            
            % form json
            json_struct = struct('date', [timestamp self.cam_timezone], ...
                                 'machine_name', self.machine_name, ...
                                 'program_name', program_name, ...
                                 'camera_id',    self.cam_id, ...
                                 'camera_time_zone', self.cam_timezone, ...
                                 'frame_num',    self.frame_num);
            json = savejson('',json_struct);
            if self.verbose > 1, json, end
            json = strrep(json, sprintf('\n'), '');
            json = strrep(json, sprintf('\t'), '');

            % credentials if present
            if ~isempty(self.server_credentials)
                cred = [' -u ' self.server_credentials];
            else
                cred = '';
            end

            % send a POST HTTP request
            %   elasticsearch index name: "download"
            %   elasticsearch type:       "status_update"
            url = ['''' self.server_address '/download/status_update/'''];
            if self.verbose > 1, url, end
            
            % call 'curl' from the command line (need unix)
            tic
            command = ['curl --max-time ' self.max_time cred ' -XPOST ' url ' -d ''' json ''''];
            if self.verbose > 1, fprintf('curl command for monitor: %s\n', command); end
            [status,cmdout] = system (command);
            t = toc;
            if self.verbose, fprintf('MonitorDownload curl took: %f sec.\n', t); end
            
            % process output
            if status == 127 && ~isempty(strfind(cmdout, 'not recognized as an internal or external command'))
                warning ('Monitor.updateDownload() failed. Curl should be installed on Windows: \n  %s', cmdout);
                success = false;
            elseif status == 0 && ~isempty(strfind(cmdout, 'error')) && ~isempty(strfind(cmdout, 'status'))
                warning ('Monitor.updateDownload() failed. Server complained: \n  %s', cmdout);
                success = false;
            elseif status ~= 0
                warning ('Monitor.updateDownload() failed. Command line call failed: \n %s', cmdout);                
                success = false;
            else
                success = true;
            end
        end
        
    end
end