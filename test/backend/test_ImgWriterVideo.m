classdef test_ImgWriterVideo < matlab.unittest.TestCase
   
    properties (Hidden)
        
        imgWriter;
        
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
            self.imgWriter = ImgWriterVideo ('relpath', '.', 'verbose', 0);
        end
        
    end    
    methods (TestMethodTeardown)
        
        function tearDown (~)
            if exist('testdata/test.avi',  'file'), delete('testdata/test.avi'); end
            if exist('testdata/test2.avi', 'file'), delete('testdata/test2.avi'); end
        end
        
    end
    methods (Test)
        
        function test_writeImpl_oneFrame (self)
            image_true = imread('testdata/Cassini/images/000000.jpg');
            self.imgWriter.writeImpl ('testdata/test.avi', image_true);
            close(self.imgWriter);
            video = vision.VideoFileReader('testdata/test.avi', ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
            [image_read, eof] = step(video);
            self.compareImages (image_read, image_true);
            self.verifyTrue (eof);
        end

        function test_writeImpl_oneVideo (self)
            image_true1 = imread('testdata/Cassini/images/000000.jpg');
            image_true2 = imread('testdata/Cassini/images/000001.jpg');
            self.imgWriter.writeImpl ('testdata/test.avi', image_true1);
            self.imgWriter.writeImpl ('testdata/test.avi', image_true2);
            close(self.imgWriter);
            video = vision.VideoFileReader('testdata/test.avi', ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
            [image_read1, eof] = step(video);
            self.compareImages (image_read1, image_true1);
            self.verifyFalse (eof);
            [image_read2, eof] = step(video);
            self.compareImages (image_read2, image_true2);
            self.verifyTrue (eof);
        end

        function test_writeImpl_manyVideo (self)
            image_true1 = imread('testdata/Cassini/images/000000.jpg');
            image_true2 = imread('testdata/Cassini/images/000001.jpg');
            image_true3 = imread('testdata/Moon/images/000000.jpg');
            image_true4 = imread('testdata/Moon/images/000001.jpg');
            self.imgWriter.writeImpl ('testdata/test.avi',  image_true1);
            self.imgWriter.writeImpl ('testdata/test2.avi', image_true3);
            self.imgWriter.writeImpl ('testdata/test.avi',  image_true2);
            self.imgWriter.writeImpl ('testdata/test2.avi', image_true4);
            close(self.imgWriter);
            
            video = vision.VideoFileReader('testdata/test.avi', ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
            [image_read1, eof] = step(video);
            self.compareImages (image_read1, image_true1);
            self.verifyFalse (eof);
            [image_read2, eof] = step(video);
            self.compareImages (image_read2, image_true2);
            self.verifyTrue (eof);
            
            video = vision.VideoFileReader('testdata/test2.avi', ...
                'ImageColorSpace','RGB','VideoOutputDataType','uint8'); 
            [image_read3, eof] = step(video);
            self.compareImages (image_read3, image_true3);
            self.verifyFalse (eof);
            [image_read4, eof] = step(video);
            self.compareImages (image_read4, image_true4);
            self.verifyTrue (eof);
        end

    end
end
