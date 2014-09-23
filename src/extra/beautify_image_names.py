#
# This script reads all .jpg images from a given dir 
#   and adds leading zeros to their names: image12.jpg -> image000012.jpg
#

import os
import sys
import glob



def beautify_image_names (image_dir, prefix, postfix):
    """
    read all .jpg files from a dir and add leading zeros to match template
    """

    os.chdir(image_dir)
    for oldname in glob.glob(prefix + "*" + postfix):
        filenum = int(oldname[len(prefix) : -len(postfix)])
        newname = prefix + ("%04d" % filenum) + postfix
        os.rename (oldname, newname)



if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print "USAGE: <image_dir>"
        sys.exit()

    image_dir = sys.argv[1];

    beautify_image_names(image_dir, "image", ".jpg")
