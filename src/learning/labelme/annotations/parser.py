# Classs to parse the labelme annotations
#
# 

import re
from spelling import SpellingCorrector
from terms import TermTree
import json
import logging
import os


class BaseParser:

    # idiotic python reference system make it necessary to be exlicit
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))

    dictionary_path = os.path.join (__location__, 'dictionary.json')

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
                    logging.info ('dictionary generalized ' + word + ' to ' + newword)

        for word in words: 
            word = str(word)
        return words



class FrameParser (BaseParser):
    ''' logic for processing individual frame '''

    def parse (self, phrase):
        words = self.to_bag_of_words(phrase)

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
        counter = 1000
        if not numbers:
            logging.debug ('added id ' + str(counter) + ' to: "' + phrase + '"')
            numbers.append(counter)
            counter += 1

        # 'car' can be skipped
        if not names:
            logging.debug ('added "car" name to: "' + phrase + '"')
            names.append('car')

        if len(names) == 1 and len(numbers) == 1:
            return names[0], numbers[0]
        else:
            return None, None




if __name__ == '__main__':
    ''' Demo '''
    parser = FrameParser ()
    print (parser.parse ('555 6 \%~~--: =%^ '))
    print (parser.parse ('LazyLinna   sleeps 10hours !!!!!11 '))
    print (parser.parse ('LazyLinna   sleeps 10hours in a bus or car !!!!!11 '))
