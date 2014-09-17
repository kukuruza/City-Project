import sys  
import cmd  
import time
import urllib.request     # can not be import urllib
import os
import io
import string
from bs4 import BeautifulSoup

url = 'http://nyctmc.org/'
usock = urllib.request.urlopen(url)   # can not be urllib.urlopen
data = usock.read()
usock.close()

soup = BeautifulSoup(data)
writeFile = open("C:/Project/videoDownload/source.txt", "w")    # can not be "\"
writeFile.write(data.decode('utf-8'))  # can not be writeFile.write(data)
writeFile.close 


def grabMultiCamera(restTime, pictureNumber):
    
    CameraId = open('C:/Project/videoDownload/camera_id.txt') 
    IDlines = CameraId.readlines()     # IDlines is a list
    
    for j in range(0, len(IDlines)):
        ID = str(IDlines[j])
        ID2 = int(ID)
        #ID2 = int(ID.split())         
        url = 'http://nyctmc.org/google_popup.php?cid='+str(ID2)
        usock2 = urllib.request.urlopen(url)   # can not be urllib.urlopen
        data2 = usock2.read()       # data2 is bytes
        usock2.close()  
    
        curfile = data2.decode('utf-8')      # curfile is string    
        num=curfile.count('\n')
        filelist = curfile.splitlines(num)
    
        keyword1 = "http://207"      #  'http://207.251.86.238/cctv501.jpg'+'?math='+Math.random()
        keyword2 = "Math.random"
    
        for i in range(1, len(filelist)):
            if keyword1 and keyword2 in filelist[i]:
                cctvline = filelist[i]

        cctvlist = cctvline.split('/')
        cctvlast = cctvlist.pop()
        IDlist = cctvlast.split("'")
    
        imgUrl = 'http://207.251.86.238/' + IDlist[0] +'?rand=Math.random()'
        directory = 'C:/Project/videoDownload/cameraNumber'+str(ID2)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for k in range(0,pictureNumber):
            urllib.request.urlretrieve(imgUrl ,"C:/Project/videoDownload/cameraNumber"+str(ID2)+"\image"+str(k)+".jpg")
            time.sleep(restTime)
        
grabMultiCamera(restTime=1, pictureNumber=120)
