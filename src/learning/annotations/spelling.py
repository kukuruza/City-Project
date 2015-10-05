# Class to correct spelling mistakes
#
# the code is a modified version of the code by the great Peter Norvig at
# http://norvig.com/spell-correct.html
#


import re, collections
import os.path
import sys

class SpellingCorrector:

    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    NWORDS = {}
    
    def __words(self, text): return re.findall('[a-z]+', text.lower()) 

    def __train_impl(self, features):
        model = collections.defaultdict(lambda: 1)
        for f in features:
            model[f] += 1
        return model

    def __edits1(self, word):
       splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
       deletes    = [a + b[1:] for a, b in splits if b]
       transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
       replaces   = [a + c + b[1:] for a, b in splits for c in self.alphabet if b]
       inserts    = [a + c + b     for a, b in splits for c in self.alphabet]
       return set(deletes + transposes + replaces + inserts)

    def __known_edits2(self, word):
        return set(e2 for e1 in self.__edits1(word) for e2 in self.__edits1(e1) if e2 in self.NWORDS)

    def __known(self, words): return set(w for w in words if w in self.NWORDS)

    def train (self, filename):
        if not os.path.isfile(filename):
            raise Exception("file " + filename + " does not exist")
        file_ = open(filename, 'r')
        self.NWORDS = self.__train_impl(self.__words(file_.read()))
        file_.close()

    def correct(self, word):
        candidates = self.__known([word]) or self.__known(self.__edits1(word)) or self.__known_edits2(word) or [word]
        return max(candidates, key=self.NWORDS.get)


if __name__ == '__main__':
    ''' Demo '''
    corrector = SpellingCorrector()
    corrector.train('dictionary.json')
    #corrector.train('data/sherlock.txt');
    while True:
        word = raw_input()
        if word == '': break
        print ('-> ' +  corrector.correct(word))
