import argparse
import json

class Car:

    def __init__ (self, bbox = None, score = None, name = None):
        assert (bbox is None or (isinstance(bbox, list) and len(bbox) == 4))
        assert (score is None or isinstance(score, float))
        assert (name is None or isinstance(name, str) or isinstance(name, unicode))

        self.bbox  = bbox
        self.score = score
        self.name  = str(name)  # possibly, from unicode

    # serialize Car as json string
    def to_json (self):
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod 
    def from_dict (d):
        bbox  = d['bbox']
        score = d['score']
        name  = d['name']
        return Car(bbox=bbox, score=score, name=name)

    # redefine how the object is printed
    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, sort_keys=True)
