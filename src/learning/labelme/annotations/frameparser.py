import logging
import baseparser

class FrameParser (baseparser.BaseParser):
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



if __name__ == '__main__':
    ''' Demo '''
    parser = FrameParser ()
    print (parser.parse ('555 6 \%~~--: =%^ '))
    print (parser.parse ('LazyLinna   sleeps 10hours !!!!!11 '))
    print (parser.parse ('LazyLinna   sleeps 10hours in a bus or car !!!!!11 '))
