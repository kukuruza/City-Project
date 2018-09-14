import os, sys, os.path as op
import re
from .spelling import SpellingCorrector
from .terms import TermTree
import json
import logging


class BaseParser:

    dictionary_path = op.join(op.dirname(op.abspath(__file__)), 'dictionary.json')

    def __init__(self):
        
        # spell checker
        self.corrector = SpellingCorrector();
        self.corrector.train (self.dictionary_path);

        # tree of terms
        file_ = open(self.dictionary_path);
        self.terms = TermTree.from_dict(json.load(file_))
        file_.close();

    def to_bag_of_words (self, phrase):

        # to lower case
        phrase = phrase.lower()

        # split numbers and words
        words = re.split (r'(\d+)', phrase)

        # remove punctuation and whitespaces
        # TODO: change this awfulness
        words1 = [];
        for word in words:
            words1 = words1 + re.findall(r"[\w']+", word)
        words = words1;

        # check words in a spellchecker (will also check numbers, whatever)
        for i, word in enumerate(words):
            words.pop(i)
            newword = self.corrector.correct(word)
            words.insert(i, newword)
            if (newword != word): 
                logging.info ('spell-checker changed ' + word + ' to ' + newword)

        # change words to more generic terms words if necessary
        for i, word in enumerate(words):
            if not word.isdigit():
                words.pop(i)
                newword = self.terms.best_match(word)
                words.insert(i, newword)
                if (newword != word):
                    if (word == 'car' and newword == 'sedan'):  # that's too much
                        logging.debug('dictionary generalized ' + word + ' to ' + newword)
                    else:
                        logging.info ('dictionary generalized ' + word + ' to ' + newword)

        for word in words: 
            word = str(word)
        return words



class FrameParser (BaseParser):
    ''' logic for processing individual frame '''

    def parse (self, phrase):
        words = self.to_bag_of_words(phrase)

        # if there are no words, only a single number, it's a sedan
        if len(words) == 1 and words[0].isdigit():
            words = ['sedan']

        # remove all numbers
        words = [word for word in words if not word.isdigit()]

        # make unique
        words = list(set(words))

        # remove 'object' if not the last word
        if len(words) > 1:
            if 'object' in words: words.remove('object')

        # zero, one, or more words left
        if not words:
            logging.warning('no words left for annotation: "' + phrase + '"')
            kind = None
        elif len(words) > 1:
            # there should be just one word left. But who knows
            logging.warning('several words left in annotation "' + phrase + 
                '". Words: "' + '", " '.join(words) + '"')
            kind = None
        else:
            # usual case
            kind = words[0];

        return kind



# should be "1 car", "1", or "car", where "1" - is digit, "car" - is word
# returns (name, number), possibly (None, None)
#
class PairParser (BaseParser):
    ''' logic for processing frame pairs '''

    # static counter
    counter = 1000

    def parse (self, phrase):
        words = self.to_bag_of_words(phrase)

        # make unique
        words = list(set(words))

        # remove all 'object'
        #words.remove('object')

        # split into words and digits
        numbers = [int(word) for word in words if word.isdigit()]
        names   = [word for word in words if not word.isdigit()]

        # remove 'object' if not the last word
        if len(names) > 1:
            if 'object' in names: names.remove('object')

        # unique ids
        if not numbers:
            logging.debug ('added id ' + str(self.counter) + ' to: "' + phrase + '"')
            numbers.append(self.counter)
            self.counter += 1

        # 'sedan' can be skipped
        if not names:
            logging.debug ('added "sedan" name to: "' + phrase + '"')
            names.append('sedan')

        if len(names) == 1 and len(numbers) == 1:
            return names[0], numbers[0]
        else:
            logging.warning ('num != 1 for either words or numbers in ' + phrase)
            return None, None




if __name__ == '__main__':
    ''' Demo '''
    parser = FrameParser ()
    while True:
        word = raw_input()
        if word == '': break
        print ('-> ' +  parser.parse(word))
