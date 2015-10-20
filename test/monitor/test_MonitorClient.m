classdef test_MonitorClient < matlab.unittest.TestCase

    properties (Hidden)
        
        monitor;
        
    end
    methods (TestMethodSetup)       
        
        function setup (self)
            
            self.monitor = MonitorClient(...
                'relpath', '.', ...
                'config_path', 'testdata/monitor_config.ini', ...
                'cam_id', 572, ...
                'verbose', 2);
        end
        
    end    
    methods (Test)
        
        function test_updateDownload (self)
            success = self.monitor.updateDownload();
            self.verifyTrue (success);
        end
   
    end
end
