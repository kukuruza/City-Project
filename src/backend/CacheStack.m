classdef CacheStack < handle
    % stack of elements (id, image), where id is char
    % It should support operations:
    %   pushWithReplace -- push and prune the stack if it's full
    %   find -- find key in the stack and get its value
    
    properties
        size
        keys
        values
        
        bottom;
        top;
    end
    methods (Hidden)
        
        function a = increment (self, a)
            a = mod(a + 1, self.size);
        end
        
    end
    methods 
        
        function self = CacheStack (size_in)
            assert (size_in > 1);
            self.size   = size_in;
            self.keys   = cell(self.size, 1);
            self.values = cell(self.size, 1);
            self.top = 0;
            self.bottom = self.size - 1;
        end
        
        function pushWithReplace (self, key, value)
            self.keys{self.top + 1} = key;
            self.values{self.top + 1} = value;
            
            self.top = self.increment(self.top);
            if self.bottom == self.top
                % discard if the stack is full
                self.bottom = self.increment(self.bottom);
            end
        end
        
        function image = find(self, key)
            % naive -- we have a small stack
            image = [];
            for i = 1 : self.size
                if strcmp(self.keys{i}, key), image = self.values{i}; end
            end
            %if ~isempty(image)
            %    image
            %end
        end
        
    end
end
