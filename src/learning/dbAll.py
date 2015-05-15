import sys, os, os.path as op

from dbManual import ManualProcessor
from dbModify import ModifyProcessor
from dbCnn import CnnProcessor
sys.path.insert(0, op.join(os.getenv('CITY_PATH'), 'src/learning/violajones'))
from dbViolajones import ViolajonesProcessor
from dbEvaluate import EvaluateProcessor

class Processor (ModifyProcessor, 
                 ManualProcessor, 
                 CnnProcessor, 
                 ViolajonesProcessor, 
                 EvaluateProcessor):
    '''
    This class inherits functions from all of the above, 
      and can be called to access them all
    '''
