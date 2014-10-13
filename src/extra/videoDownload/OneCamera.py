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

def grabOneCamera(cameraNumber, restTime, pictureNumber):
    url = 'http://nyctmc.org/google_popup.php?cid='+str(cameraNumber)
    usock2 = urllib.request.urlopen(url)   # can not be urllib.urlopen
    data2 = usock2.read()       # data2 is bytes
    usock2.close()

    #soup2 = BeautifulSoup(data2)
    writeFile = open("C:/Project/videoDownload/Camerasource2.txt", "w")    # can not be "\"
    writeFile.write(data2.decode('utf-8'))  # can not be writeFile.write(data)
    writeFile.close 
    
    
    curfile = data2.decode('utf-8')      # curfile is string    
    num=curfile.count('\n')
    filelist = curfile.splitlines(num)
    
    keyword1 = "http://207"      #  'http://207.251.86.238/cctv501.jpg'+'?math='+Math.random()
    keyword2 = "Math.random"
 
    #curfile = open('C:/Project/videoDownload/Camerasource2.txt')   
    #cctvline = ""
    #for line in curfile.readlines():              #curfile.readlines()
    #    if keyword1 and keyword2 in line:
    #        cctvline = str(line)
    
    for i in range(1, len(filelist)):
        if keyword1 and keyword2 in filelist[i]:
            cctvline = filelist[i]

    cctvlist = cctvline.split('/')
    cctvlast = cctvlist.pop()
    IDlist = cctvlast.split("'")
    
    imgUrl = 'http://207.251.86.238/' + IDlist[0] +'?rand=Math.random()'
    directory = 'C:/Project/videoDownload/cameraNumber'+str(cameraNumber)
    if not os.path.exists(directory):
        os.makedirs(directory)
    for i in range(0,pictureNumber):
        urllib.request.urlretrieve(imgUrl ,"C:/Project/videoDownload/cameraNumber"+str(cameraNumber)+"\image"+str(i)+".jpg")
        time.sleep(restTime)
        
grabOneCamera(cameraNumber=556, restTime=1, pictureNumber=10)
