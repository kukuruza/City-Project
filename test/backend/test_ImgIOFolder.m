classdef test_ImgIOFolder < matlab.unittest.TestCase
   
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
    methods (TestMethodSetup)       
        
        function setup (self)
            self.imgIO = ImgIOFolder('relpath', '.');
        end
        
    end    
    methods (Test)
        
        function test_readImpl (self)
            image = self.imgIO.readImpl('testdata/Cassini/images/000000.jpg');
            self.verifyEqual (size(image), [100,100,3]);
        end
        
        %function test_badImagefile (self)
        %    self.setup()
        %    self.verifyError (@()self.img_io.readImpl('dummyname'), 'badpath')
        %end
        
        function test_writeImpl (self)
            image1 = imread('testdata/Cassini/images/000000.jpg');
            imagepath = 'testdata/test/image.jpg';
            self.imgIO.writeImpl (image1, imagepath);
            image2 = imread (imagepath);
            self.verifyNotEmpty (image2)
            self.compareImages (image1, image2);
            rmdir('testdata/test', 's');
        end
        
        function test_imread (self)
            image = self.imgIO.imread('testdata/Cassini/images/000000.jpg');
            self.verifyNotEmpty (image);
            self.verifyEqual (size(image), [100, 100, 3]);            
        end
        
        function test_imread_cacheUpdates (self)
            self.imgIO.imread ('testdata/Cassini/images/000000.jpg');
            self.assertEqual (length(keys(self.imgIO.image_cache)), 1);
            self.assertTrue (isKey(self.imgIO.image_cache, 'testdata/Cassini/images/000000.jpg'));

            self.imgIO.imread ('testdata/Cassini/images/000001.jpg');
            self.assertEqual (length(keys(self.imgIO.image_cache)), 1);
            self.assertTrue (isKey(self.imgIO.image_cache, 'testdata/Cassini/images/000001.jpg'));
        end

        function test_imread_cacheLoads (self)
            image1path = 'testdata/Cassini/images/000000.jpg';
            self.imgIO.imread (image1path);
            imageRead = self.imgIO.imread (image1path);
            imageTrue = imread (image1path);
            self.compareImages (imageRead, imageTrue);
            self.assertEqual (length(keys(self.imgIO.image_cache)), 1);
            self.assertTrue (isKey(self.imgIO.image_cache, image1path));
        end
        
        function test_maskread (self)
            mask = self.imgIO.maskread('testdata/Cassini/masks/000000.png');
            self.verifyNotEmpty (mask);
            self.verifyEqual (size(mask), [100, 100]);            
        end
        
        function test_maskread_cacheUpdates (self)
            self.imgIO.maskread ('testdata/Cassini/masks/000000.png');
            self.assertEqual (length(keys(self.imgIO.mask_cache)), 1);
            self.assertTrue (isKey(self.imgIO.mask_cache, 'testdata/Cassini/masks/000000.png'));

            self.imgIO.maskread ('testdata/Cassini/masks/000001.png');
            self.assertEqual (length(keys(self.imgIO.mask_cache)), 1);
            self.assertTrue (isKey(self.imgIO.mask_cache, 'testdata/Cassini/masks/000001.png'));
        end

        function test_maskread_cacheLoads (self)
            mask1path = 'testdata/Cassini/masks/000000.png';
            self.imgIO.maskread (mask1path);
            maskRead = self.imgIO.maskread (mask1path);
            maskTrue = imread (mask1path);
            self.compareImages (maskRead, maskTrue);
            self.assertEqual (length(keys(self.imgIO.mask_cache)), 1);
            self.assertTrue (isKey(self.imgIO.mask_cache, mask1path));
        end
        
        function test_imwrite (self)
            imagepath = 'testdata/test/image.jpg';
            image1 = imread('testdata/Cassini/images/000000.jpg');
            self.imgIO.imwrite (image1, imagepath);
            image2 = imread (imagepath);
            self.verifyNotEmpty (image2);
            self.compareImages (image1, image2);
            rmdir('testdata/test', 's');
        end

        function test_maskwrite (self)
            imagepath = 'testdata/test/mask.png';
            mask1 = imread('testdata/Cassini/masks/000000.png');
            self.imgIO.maskwrite (mask1, imagepath);
            mask2 = imread (imagepath);
            self.verifyNotEmpty (mask2);
            self.compareImages (mask1, mask2);
            rmdir('testdata/test', 's');
        end 

    end
end
