classdef test_ImgIOVideo < matlab.unittest.TestCase
   
    properties (Hidden)
        
        imgIO;
        
    end
    methods (Hidden)
        
        function diff = compareImages (self, image1, image2)
            self.verifyEqual (size(image1), size(image2));
            diff = single(abs(image1-image2));
            summ = single(image1+image2);
            % 'almost' because of JPEG compression
            self.verifyLessThan (sum(diff(:)) / sum(summ(:)), 0.05);
        end 
        
    end
    methods (TestClassSetup)
    
        % clear all for convinience
        function setupOnce(~)
            %clc
        end
        
    end        
    methods (TestMethodSetup)
        
        function setup (self)
            self.imgIO = ImgReaderVideo ('relpath', '.', 'verbose', 0);
        end
        
    end    
    methods (TestMethodTeardown)
        
        function tearDown (self)
            self.imgIO.close()
        end
        
    end
    methods (Test)
        
        function test_readImpl (self)
            image_read = self.imgIO.readImpl('testdata/Cassini/images/000000.jpg', false);
            image_true = imread('testdata/Cassini/images/000000.jpg');
            self.compareImages (image_read, image_true);
        end

        function test_readImpl_takeCached (self)
                         self.imgIO.readImpl('testdata/Cassini/images/000001.jpg', false);
            self.assertEqual (self.imgIO.image_cache.top, 2);
            image_read = self.imgIO.readImpl('testdata/Cassini/images/000001.jpg', false);
            image_true = imread('testdata/Cassini/images/000001.jpg');
            self.compareImages (image_read, image_true);
            self.assertEqual (self.imgIO.image_cache.top, 2);
        end
        
        % test past the end
        
        % test before expected_frame
        
        function test_readImpl_nonsequential1 (self)
            image_read = self.imgIO.readImpl('testdata/Moon/images/000001.jpg', false);
            image_true = imread('testdata/Moon/images/000001.jpg');
            self.compareImages (image_read, image_true);
            self.assertEqual (self.imgIO.image_cache.top, 2);
        end
        
        function test_readImpl_nonsequential2 (self)
                         self.imgIO.readImpl('testdata/Moon/images/000000.jpg', false);
            image_read = self.imgIO.readImpl('testdata/Moon/images/000002.jpg', false);
            image_true = imread('testdata/Moon/images/000002.jpg');
            self.compareImages (image_read, image_true);
            self.assertEqual (self.imgIO.image_cache.top, 3);
        end

        function test_readImpl_stackloop (self)
            self.imgIO.close()
            self.imgIO = ImgReaderVideo ('relpath', '.', 'cache_size', 2);
                         self.imgIO.readImpl('testdata/Moon/images/000000.jpg', false);
                         self.imgIO.readImpl('testdata/Moon/images/000001.jpg', false);
            image_read = self.imgIO.readImpl('testdata/Moon/images/000002.jpg', false);
            image_true = imread('testdata/Moon/images/000002.jpg');
            self.compareImages (image_read, image_true);
            self.assertEqual (self.imgIO.image_cache.top, 1);
        end

        function test_imread (self)
            image_read = self.imgIO.imread('testdata/Moon/images/000000.jpg');
            image_true = imread('testdata/Moon/images/000000.jpg');
            self.compareImages (image_read, image_true);
        end

        function test_imread_cached (self)
                         self.imgIO.imread('testdata/Moon/images/000000.jpg');
                         self.imgIO.imread('testdata/Moon/images/000001.jpg');
            image_read = self.imgIO.imread('testdata/Moon/images/000000.jpg');
            image_true = imread('testdata/Moon/images/000000.jpg');
            self.compareImages (image_read, image_true);
        end

        function test_maskread (self)
            mask_read = self.imgIO.maskread('testdata/Moon/masks/000000.png');
            mask_true = imread('testdata/Moon/masks/000000.png') > 128;
            self.assertTrue (islogical(mask_read))
            self.compareImages (mask_read, mask_true);
        end

        function test_maskread_cached (self)
                         self.imgIO.maskread('testdata/Moon/masks/000000.png');
                         self.imgIO.maskread('testdata/Moon/masks/000001.png');
            mask_read = self.imgIO.maskread('testdata/Moon/masks/000000.png');
            mask_true = imread('testdata/Moon/masks/000000.png') > 128;
            self.assertTrue (islogical(mask_read))
            self.compareImages (mask_read, mask_true);
        end

    end
end
