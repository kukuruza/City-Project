import sys  
import cmd  
import time
import urllib.request     # can not be import urllib
import os
import io
import string
from bs4 import BeautifulSoup

# Get open_window ID
keyword = "open_window"
keyLinksFile5 = open("C:/Project/videoDownload/keyLinksFile5.txt","w")
curfile = open('C:/Project/videoDownload/chtml.txt')
for line in curfile.readlines():
    if keyword in line:
        keyLinksFile5.write(line+"\n") 
keyLinksFile5.close
     

lines = list(open("C:/Project/videoDownload/keyLinksFile5.txt"))

keyLinksFile6 = open("C:/Project/videoDownload/keyLinksFile6.txt","w")     # all the lines with open_window
for i in range(0,440):
    keyLinksFile6.write(lines[2+i*4]) 
keyLinksFile6.close                         

keyLinksFile7 = open("C:/Project/videoDownload/keyLinksFile7.txt","w")     # all the lines with address
for i in range(0,440):
    keyLinksFile7.write(lines[i*4]) 
keyLinksFile7.close




# print(lines[8])












#soup = BeautifulSoup(doc)
#keyLinksFile2 = open("C:/Project/videoDownload/keyLinksFile2.txt","w")
#imgLinks = soup.find_all("img")   # the attribute of imaLinks is list
#for row in imgLinks:
#    keyLinksFile2.write(str(row)+"\n")  # the attribute of each row is tag, must convert into string in order to write to file 
#    keyLinksFile2.close
    

#keyLinksFile3 = open("C:/Project/videoDownload/keyLinksFile3.txt","w")
#for eachImgLink in imgLinks:
#    if eachImgLink['src'].startswith("http://207"):
#        keyLinksFile3.write(eachImgLink['src']+"\n")
#        keyLinksFile3.close

