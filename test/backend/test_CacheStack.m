classdef test_CacheStack < matlab.unittest.TestCase

    properties (Hidden)
        
        cache;
        
    end
    methods (TestMethodSetup)       
        
        function setup (self)
            self.cache = CacheStack(2);
        end
        
    end    
    methods (Test)
        
        function test_push_simple (self)
            self.verifyEqual (self.cache.size, 2);
            self.verifyEqual (self.cache.bottom, 1);
            self.verifyEqual (self.cache.top, 0);

            self.cache.pushWithReplace ('a', 10);
            self.verifyEqual (self.cache.bottom, 0);
            self.verifyEqual (self.cache.top, 1);
            self.verifyEqual (self.cache.keys{1}, 'a');
            self.verifyEqual (self.cache.values{1}, 10);
            self.verifyEqual (self.cache.find('a'), 10);
            self.verifyEqual (self.cache.find('d'), []);
        end
        
        function test_push_cycle (self)
            self.cache.pushWithReplace ('a', 10);
            self.cache.pushWithReplace ('b', 20);
            self.verifyEqual (self.cache.bottom, 1);
            self.verifyEqual (self.cache.top, 0);
            self.verifyEqual (self.cache.keys{1}, 'a');
            self.verifyEqual (self.cache.keys{2}, 'b');
            self.verifyEqual (self.cache.values{1}, 10);
            self.verifyEqual (self.cache.values{2}, 20);
            self.verifyEqual (self.cache.find('a'), 10);
            self.verifyEqual (self.cache.find('b'), 20);
            self.verifyEqual (self.cache.find('d'), []);
        end
        
        function test_push_replace (self)
            self.cache.pushWithReplace ('a', 10);
            self.cache.pushWithReplace ('b', 20);
            self.cache.pushWithReplace ('c', 30);
            self.verifyEqual (self.cache.bottom, 0);
            self.verifyEqual (self.cache.top, 1);
            self.verifyEqual (self.cache.keys{1}, 'c');
            self.verifyEqual (self.cache.keys{2}, 'b');
            self.verifyEqual (self.cache.values{1}, 30);
            self.verifyEqual (self.cache.values{2}, 20);
            self.verifyEqual (self.cache.find('a'), []);
            self.verifyEqual (self.cache.find('b'), 20);
            self.verifyEqual (self.cache.find('c'), 30);
            self.verifyEqual (self.cache.find('d'), []);
        end
   
    end
end
