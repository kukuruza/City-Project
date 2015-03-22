import os, os.path as op
import re
import shutil
import zipfile

num_thresh = 10

def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))

if (not os.environ.get('CITY_DATA_PATH') or 
    not os.environ.get('CITY_PATH') or
    not os.environ.get('CITY_SHARED_PATH')):
    raise Exception ('Set environmental variables CITY_PATH, CITY_DATA_PATH, CITY_SHARED_PATH')

rootdir = os.getenv('CITY_DATA_PATH')
tmpdir  = op.join (os.getenv('CITY_PATH'), 'tmp')
#shareddir = os.getenv('CITY_SHARED_PATH')
print ('data dir: ' + rootdir)
print ('temp dir: ' + tmpdir)
#print ('shared dir: ' + shareddir)

num_files = sum([len(files) for r, d, files in os.walk(rootdir)])
print ('data has ' + str(num_files) + ' files and dirs')

if op.exists(tmpdir):
    print ('will overwrite temp dir')
    shutil.rmtree(tmpdir)
print ('start copying data to the temp location')
shutil.copytree (rootdir, tmpdir)

compress_ext = '(\.jpg|\.jpeg|\.tiff|\.tif|\.png|\.mat|\.xml)$'

print ('start compressing directories with more than ' + str(num_thresh) + ' images')
for dirpath, dirnames, filenames in os.walk(tmpdir):
    are_images = [re.search(compress_ext, filename) for filename in filenames]
    counter = len([x for x in are_images if x is not None])
    if counter > num_thresh:
        print ('compressing ' + dirpath)
        zipf = zipfile.ZipFile(dirpath + '.zip', 'w')
        zipdir(dirpath, zipf)
        zipf.close()
        shutil.rmtree(dirpath)

num_files = sum([len(files) for r, d, files in os.walk(tmpdir)])
print ('tmpdir has ' + str(num_files) + ' files and dirs')

#if op.exists(shareddir):
#    shutil.rmtree(shareddir)
#print ('moving tmpdir to shareddir')
#shutil.move (tmpdir, shareddir)
