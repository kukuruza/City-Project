#
# This script reads .jpg images from a given dir sequentially
#   and deletes those which are duplicates of the previous ones
#

import os
import sys
import glob
import filecmp



def filter_dupl_images (image_dir, prefix, postfix):
    """
    read .jpg files from a dir and filter duplicates
    """

    os.chdir(image_dir)
    filenames = glob.glob(prefix + "*" + postfix)
    for i in range(len(filenames)-1):
        filename1 = filenames[i];
        filename2 = filenames[i+1];
        # compare the files pairwise
        if filecmp.cmp(filename1, filename2, shallow=False):
            # remove the first file from the pair
            sys.stdout.write ('1')
            os.remove(filename1)
        else:
            sys.stdout.write ('0')
    print ''



if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print "USAGE: <image_dir>"
        sys.exit()

    image_dir = sys.argv[1];

    filter_dupl_images(image_dir, "image", ".jpg")
