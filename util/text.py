from __future__ import absolute_import, division, print_function

import codecs
import re

import numpy as np

from six.moves import range

class Alphabet(object):
    def __init__(self, config_file):
        self._config_file = config_file
        self._label_to_str = []
        self._str_to_label = {}
        self._size = 0
        with codecs.open(config_file, 'r', 'utf-8') as fin:
            for line in fin:
                if line[0:2] == '\\#':
                    line = '#\n'
                elif line[0] == '#':
                    continue
                self._label_to_str += line[:-1] # remove the line ending
                self._str_to_label[line[:-1]] = self._size
                self._size += 1

    def _string_from_label(self, label):
        return self._label_to_str[label]

    def _label_from_string(self, string):
        try:
            return self._str_to_label[string]
        except KeyError as e:
            raise KeyError(
                'ERROR: Your transcripts contain characters (e.g. \'{}\') which do not occur in data/alphabet.txt! Use ' \
                'util/check_characters.py to see what characters are in your [train,dev,test].csv transcripts, and ' \
                'then add all these to data/alphabet.txt.'.format(string)
            ).with_traceback(e.__traceback__)

    def encode(self, string):
        res = []
        for char in string:
            res += self._label_from_string(char)
        return res

    def decode(self, labels):
        res = ''
        for label in labels:
            res += self._string_from_label(label)
        return res

    def size(self):
        return self._size

    def config_file(self):
        return self._config_file


def text_to_char_array(series, alphabet):
    r"""
    Given a Pandas Series containing transcript string, map characters to
    integers and return a numpy array representing the processed string.
    """
    try:
        series['transcript'] = np.asarray(alphabet.encode(series['transcript']))
    except KeyError as e:
        # Provide the row context (especially wav_filename) for alphabet errors
        raise ValueError(str(e), series)

    if series['transcript'].shape[0] == 0:
        raise ValueError("Found an empty transcript! You must include a transcript for all training data.", series)

    return series


# The following code is from: http://hetland.org/coding/python/levenshtein.py

# This is a straightforward implementation of a well-known algorithm, and thus
# probably shouldn't be covered by copyright to begin with. But in case it is,
# the author (Magnus Lie Hetland) has, to the extent possible under law,
# dedicated all copyright and related and neighboring rights to this software
# to the public domain worldwide, by distributing it under the CC0 license,
# version 1.0. This software is distributed without any warranty. For more
# information, see <http://creativecommons.org/publicdomain/zero/1.0>

def levenshtein(a, b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a, b = b, a
        n, m = m, n

    current = list(range(n+1))
    for i in range(1, m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1, n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)

    return current[n]

# Validate and normalize transcriptions. Returns a cleaned version of the label
# or None if it's invalid.
def validate_label(label):
    # For now we can only handle [a-z ']
    if re.search(r"[0-9]|[(<\[\]&*{]", label) is not None:
        return None

    label = label.replace("-", " ")
    label = label.replace("_", " ")
    label = re.sub("[ ]{2,}", " ", label)
    label = label.replace(".", "")
    label = label.replace(",", "")
    label = label.replace("?", "")
    label = label.replace("\"", "")
    label = label.strip()
    label = label.lower()

    return label if label else None
