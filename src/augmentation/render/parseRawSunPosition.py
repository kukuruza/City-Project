import sys, os, os.path as op
sys.path.insert(0, os.path.join(os.getenv('CITY_PATH'), 'src'))
import os, os.path as op
import datetime
import pprint
import cPickle
from learning.helperSetup import atcity

txt_file = 'data/augmentation/resources/sun_position.txt'
bin_file = 'data/augmentation/resources/sun_position.pkl'


with open(atcity(txt_file)) as f:
  lines = f.readlines()
  lines = lines[9:]

positions = {}

for line in lines:
  (daystr, clockstr, altitude, azimuth) = tuple(line.split())
  (month, day) = tuple(daystr.split('/'))
  (hour, minute) = tuple(clockstr.split(':'))

  date = datetime.datetime (year=2015, month=int(month), day=int(day), 
                            hour=int(hour), minute=int(minute))

  positions[date] = (float(altitude), float(azimuth))


with open(atcity(bin_file), 'wb') as f:
  cPickle.dump(positions, f, cPickle.HIGHEST_PROTOCOL)

# test

date = datetime.datetime (year=2015, month=6, day=14, hour=15, minute=45)

with open(atcity(bin_file), 'rb') as f:
  data = cPickle.load(f)
pprint.pprint(data[date])
