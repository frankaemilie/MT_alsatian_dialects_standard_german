# -*- coding: utf-8 -*-

"""
Python module to tokenise texts in Alsatian

Installation:
=============
Put the module in a directory listed in the Python path.

Usage:
======
Example::
    import alsatian_tokeniser
    # (1) build a tokeniser object 
    ret = alsatian_tokeniser.RegExpTokeniser()
    # (2) tokenise text
    tokens = ret.tokenise(my_alsatian_text)
    # (3) print tokenised text
    print tokens

The module can be used as a command line tool too, for more information
ask for module help::
    python alsatian_tokeniser.py --help

@author: Delphine Bernhard (dbernhard@unistra.fr)
@version: 1.4.1
"""

import codecs
import re
import sys

# The regular expressions here have been inspired from Gregory Grefenstette's
# Corpora List Message dated Fri, 16 Oct 1998 
# (http://torvald.aksis.uib.no/corpora/1998-4/0035.html)
# and also inspired from TreeTaggerWrapper by Laurent Pointal
always_sep = r'(\?|¿|!|;|\*|¤|°|\|¦|\(|\)|\\|\[|\]|\{|_|"|“|”|«|»|„|&|#|~|=|—|\+|–|©|―|®|–|-(?=t-))'
# Language-dependent regular expressions
begin_sep = r"(``|[dszn]['`’´‘-](?!r )|[uùü][fn]['`’´‘](?! )|z[ìi]tter['`’´‘](?! )|mit(?='))"
end_sep = r"(-|,|:|['`’´‘]d|(?<=un)['`’´‘]r|(?<!\b[dm])(?<=['`’´‘])[m]['`’´‘][r]|(?<!\b[dm])(?<!['`’´‘][m])['`’´‘][ms]a?|(?<=dàss)['`’´‘]r|(?<=hàt)['`’´‘]r|(?<=ìn)['`’´‘]r[a]?|(?<!\b[dm])(?<!['`’´‘][e])['`’´‘]me|(?<!\b[dm])(?<=-)un)"
middle_sep = r'(-n-)'
numbers = r'^(<|>)?([0-9IVXLCDM]+[ |.]?)+[0-9]?([,][0-9]+)?$'
abbrev1 = r'(Bd\.|Chr\.|Fr\.|hochdt\.|frz\.|latiin\.|St\.|co\.|ca\.|corp\.|vs\.|e\.g\.|etc\.|ex\.|cf\.|eg\.|jan\.|feb\.|mar\.|apr\.|jun\.|jul\.|aug\.|sep\.|sept\.|oct\.|nov\.|dec\.|ed\.|eds\.|repr\.|trans\.|vol\.|vols\.|rev\.|b\.|m\.|bur\.|d\.|r\.|dept\.|mm\.|u\.|mr\.|jr\.|ms\.|mme\.|mrs\.|dr\.|st\.)'
# End of language-dependent regular expressions
abbrev2 = r'(\w\.(\w\.)*)'
abbrev3 = r'([A-Z]\.[A-Z][bcdfghi-np-tvxz]+\.)'
url = r'((https?://)?([^ .]+\.){2,}([^ ])+)'
email = r'[A-Z0-9._%-]+@[A-Z0-9._%-]+\.[A-Z]{2,4}'
inseparable = [u"d'r", u"widd'r", u"z'erscht", u"z'r", u"f'r", u"z'rüeck"]
# Token types with their string representation
types = {'word': 0, 'separator': 1, 'number': 2,
         'abbreviation': 3, 'url': 4, 'email': 5}


# ==============================================================================
class TokeniserIOError(Exception):
    """This exception can occur if there is an input-output problem"""

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


# ==============================================================================
class Paragraph:
    """
    Class representing a paragraph
    @ivar  sentences: Sentences contained in the paragraph
    @type sentences: list of Sentence objects
    """

    def __init__(self):
        self.sentences = []

    def get_sentences(self):
        """
        Returns the list of sentences
        @return: List of sentences
        @rtype:  List of Sentence objects
        """
        return self.sentences

    def add_sentence(self, sentence):
        """
        Adds a Sentence to the list of sentences
        
        @param sentence: sentence to add in the paragraph
        @type sentence: Sentence
        """
        self.sentences.append(sentence)

    def remove_last_sentence(self):
        """
        Removes the last sentence from the list of sentences
        """
        self.sentences.pop()

    def get_contents(self):
        s = u'\n'
        strs = [tok.get_contents() for tok in self.sentences]
        return s.join(strs)

    def __str__(self, encoding="utf-8"):
        return self.__unicode__().encode(encoding)

    def __unicode__(self):
        return self.get_contents()


# ==============================================================================
class Sentence:
    """
    Class representing a sentence
    @ivar tokens: tokens contained in the sentence
    @type tokens: list of Token objects
    """

    def __init__(self):
        self.tokens = []

    def get_tokens(self):
        """
        Returns the list of words
        
        @return: List of words
        @rtype:  List of Word objects
        """
        return self.tokens

    def get_length(self):
        """
        Returns the number of words in the sentence
        
        @return: Number of words in the sentence
        @rtype:  integer
        """
        return len(self.tokens)

    def add_token(self, token):
        """
        Adds a Token to the list of tokens
        
        @param token: token to add in the sentence
        @type token: Token
        """
        w = str(token)
        if len(w) > 0 and not w.isspace():
            self.tokens.append(token)

    def get_contents(self):
        strs = [tok.get_contents() for tok in self.tokens]
        return ' '.join(strs)

    def __str__(self, encoding="utf-8"):
        return self.get_contents()

    def __unicode__(self):
        return self.get_contents()


# ==============================================================================
class Token:
    """
    Class representing a token
    @ivar  token: token
    @type token: string
    @ivar  t_type: token type
    @type t_type: integer
    """

    def __init__(self, contents, _type=0):
        self.token = contents
        self.t_type = _type

    def __str__(self, encoding="utf-8"):
        return self.token

    def __unicode__(self):
        return self.token

    def get_contents(self):
        return self.token


# ==============================================================================
class Text:
    """
    Class representing a text : it contains paragraphs
    @ivar  paragraphs: paragraphs contained in the text
    @type paragraphs: list of Paragraph objects
    """

    def __init__(self):
        self.paragraphs = []

    def add_paragraph(self, pt):
        """
        Adds a Paragraph to the list of paragraphs
        
        @param pt: paragraph to add in the text
        @type pt: Paragraph
        """
        self.paragraphs.append(pt)

    def get_paragraphs(self):
        """
        Returns the list of paragraphs
        
        @return: List of paragraphs
        @rtype:  List of Paragraph objects
        """
        return self.paragraphs

    def get_sentences(self):
        """
        Returns the list of sentences
        
        @return: List of sentences
        @rtype:  List of Sentence objects
        """
        sentences = []
        for p in self.paragraphs:
            for s in p.get_sentences():
                sentences.append(s)
        return sentences

    def get_tokens(self):
        """
        Returns the list of words
        
        @return: List of words
        @rtype:  List of Word objects
        """
        tokens = []
        for s in self.get_sentences():
            for w in s.get_tokens():
                tokens.append(w)
        return tokens

    def get_contents(self):
        res = u''
        for p in self.paragraphs:
            sentences = p.get_sentences()
            if len(sentences) > 0:
                for s in sentences:
                    res = res + s.get_contents().rstrip()
                    res = res.rstrip() + u'\n'
                # res = res + u'\n'
        return res

    def __str__(self, encoding="utf-8"):
        return self.__unicode__().encode(encoding)

    def __unicode__(self):
        return self.get_contents()

    def to_XML(self):
        """
        Returns an XML representation of the text's tokens
        
        @return: XML representation of the text's tokens
        @rtype:  string
        """
        res = ''
        p_index = 0
        s_index = 0
        for p in self.paragraphs:
            sentences = p.get_sentences()
            if len(sentences) > 0:
                res += "<p id=\"p-" + str(p_index) + "\">" + '\n'
                p_index += 1
                for s in sentences:
                    tokens = s.get_tokens()
                    if len(tokens) > 0:
                        res += "\t<s id=\"s-" + str(s_index) + "\"> "
                        s_index += 1
                        for w in tokens:
                            res += "<w>" + w.get_contents() + "</w> "
                        res += "</s>" + '\n'
                res += "</p>" + '\n'
        return res

    def to_lines(self):
        """
        Returns an string representation of the text's tokens with one token per
        line
        
        @return: string representation of the text's tokens with one token per
        line
        @rtype:  string
        """
        res = ''
        for p in self.paragraphs:
            sentences = p.get_sentences()
            if len(sentences) > 0:
                for s in sentences:
                    tokens = s.get_tokens()
                    if len(tokens) > 0:
                        for w in tokens:
                            res += w.get_contents().rstrip() + '\n'
                        # res += '\n'
                # res += '\n'
        return res


# ==============================================================================
class Tokeniser(object):
    """Base class for all tokenisers"""

    def __init__(self):
        pass

    def tokenise(self, text):
        """
        Tokenises a text
        """
        pass

    @staticmethod
    def add_token(token, sentence, t_type=0):
        """
        Adds a Token to the current sentence
        
        @param token: token to add to the sentence
        @type token: string
        @param sentence: sentence to which the word will be added
        @type sentence: Sentence
        @param t_type: token type
        @type t_type: integer
        """
        wt = Token(token, t_type)
        sentence.add_token(wt)


# ==============================================================================
class RegExpTokeniser(Tokeniser):
    """ 
    Tokeniser based on regular expressions which are language dependent
    """

    def __init__(self):
        """
        Constructor for the RegExpTokeniser object
        """
        super().__init__()
        self.ab1_re = re.compile(abbrev1, re.IGNORECASE)
        self.ab2_re = re.compile(abbrev2)
        self.ab3_re = re.compile(abbrev3)
        self.num_re = re.compile(numbers)
        self.url_re = re.compile(url)
        self.mail_re = re.compile(email, re.IGNORECASE)
        self.non_sep = set(inseparable)

    def tokenise(self, text):
        """
        Tokenises a text
        @param text: text to tokenise
        @type text: string
        @return: Text object
        @rtype:  Text
        """
        t = Text()
        text = RegExpTokeniser._handle_always_sep(always_sep, text)
        text = RegExpTokeniser._handle_end_sep(end_sep, text)
        text = RegExpTokeniser._handle_begin_sep(begin_sep, text)
        text = RegExpTokeniser._handle_sometimes_sep(text)
        text = RegExpTokeniser._handle_middle_sep(middle_sep, text)
        paragraphs = text.split('\n')
        for i in range(len(paragraphs)):
            p = self._build_sentences(paragraphs[i])
            t.add_paragraph(p)
        return t

    def _build_sentences(self, paragraph):
        tokens = paragraph.split()
        p: Paragraph = Paragraph()
        s = Sentence()
        i = 0
        while i < len(tokens):
            token = tokens[i]
            point = token.find('.') != -1
            three_points = token.find(u'…') != -1 or token.find(u"...") != -1
            comma = token.find(',')
            mark = token == "?" or token == "!"
            dash = token.find('/')
            ab1_match = 0
            ab2_match = 0
            ab3_match = 0
            url_match = 0
            mail_match = 0
            if point:
                ab1_match = not self.ab1_re.match(token) is None
                ab2_match = not self.ab2_re.match(token) is None
                ab3_match = not self.ab3_re.match(token) is None
                url_match = not self.url_re.match(token) is None
                mail_match = not self.mail_re.match(token) is None
            num_match = not self.num_re.match(token) is None
            if mark:
                self.add_token(token, s, types['separator'])
                if (len(tokens) - 1) > i > 0 and \
                        tokens[i - 1] != '(' and tokens[i + 1] != ')':
                    self.check_sentence(s)
                    p.add_sentence(s)
                    s = Sentence()
            elif comma != -1:
                if comma == (len(token) - 1):
                    if num_match:
                        self.add_token(token[0:comma], s, types['number'])
                    else:
                        self.add_token(token[0:comma], s, self._get_type(token[0:comma]))
                    self.add_token(",", s, types['separator'])
                elif not num_match:  # cas de l'espace manquant après la virgule
                    self.add_token(token[0:comma], s, self._get_type(token[0:comma]))
                    self.add_token(",", s, types['separator'])
                    self.add_token(token[comma + 1:], s, self._get_type(token[comma + 1:]))
            elif (point or three_points) \
                    and not ab1_match \
                    and not ab2_match \
                    and not ab3_match \
                    and not num_match \
                    and not url_match \
                    and not mail_match:
                if (point and token.rfind('.') == (len(token) - 1)) \
                        or (three_points and token.rfind(u'...') == (len(token) - 1)) \
                        or (three_points and token.rfind(u'…') == (len(token) - 1)):
                    token = token.replace(u'.', u'')
                    token = token.replace(u'…', u'')
                    close_punct = False
                    if i < (len(tokens) - 1):
                        close_punct = tokens[i + 1] in '"”)]'
                    self.add_token(token, s, self._get_type(token))
                    if not three_points:
                        self.add_token(u'.', s, types['separator'])
                    else:
                        self.add_token(u"…", s, types['separator'])
                    if close_punct:
                        self.add_token(tokens[i + 1], s, types['separator'])
                        i += 1
                    if i < (len(tokens) - 1):
                        self.check_sentence(s)
                        p.add_sentence(s)
                        s = Sentence()
                else:
                    word = ''
                    sep = ''
                    for j in range(len(token)):
                        if token[j] == u'.' or token[j] == u'…':
                            sep = sep + token[j]
                            if len(word) > 0:
                                self.add_token(word, s, self._get_type(word))
                                word = u''
                        else:
                            word = word + token[j]
                            if len(sep) > 0:
                                self.add_token(sep, s, types['separator'])
                                sep = u''
                    self.add_token(word, s, self._get_type(word))
            elif dash != -1 and not url_match:
                t1 = token[0:dash]
                t2 = token[dash + 1:]
                if t1.isdigit() and t2.isdigit():
                    self.add_token(token, s, self._get_type(token))
                else:
                    self.add_token(t1, s, self._get_type(t1))
                    self.add_token('/', s, types['separator'])
                    self.add_token(t2, s, self._get_type(t2))
            else:
                if num_match:
                    # Cas des dates en fin de phrase
                    if point and token.rfind('.') == (len(token) - 1) and len(token) == 5:
                        self.add_token(token[:-1], s, types['number'])
                        self.add_token(u'.', s, types['separator'])
                        if i < (len(tokens) - 1):
                            self.check_sentence(s)
                            p.add_sentence(s)
                            s = Sentence()
                    else:
                        self.add_token(token, s, types['number'])
                elif ab1_match or ab2_match or ab3_match:
                    self.add_token(token, s, types['abbreviation'])
                elif url_match:
                    self.add_token(token, s, types['url'])
                elif mail_match:
                    self.add_token(token, s, types['email'])
                else:
                    self.add_token(token, s)
            i += 1
        self.check_sentence(s)
        p.add_sentence(s)
        return p

    # Merge over-tokenized units (cf. https://github.com/boudinfl/kea/blob/master/kea/kea.py)
    def check_sentence(self, s):
        i = 0
        tokens = s.tokens
        temp_list = []
        while i < len(tokens):
            current_tok = tokens[i]
            j = i + 1
            while j <= len(tokens):
                candidate = ''
                for k in range(i, j):
                    candidate += tokens[k].get_contents()
                if candidate.lower() in self.non_sep:
                    # Go to the last word
                    i = j - 1
                    # Replace the current token with the candidate
                    current_tok = Token(candidate, tokens[k].t_type)
                    break
                j += 1
            # Add the current token to the temporary list
            temp_list.append(current_tok)
            i += 1
        s.tokens = temp_list

    @staticmethod
    def _handle_always_sep(regexp, text):
        p = re.compile(regexp, re.IGNORECASE | re.UNICODE)
        text = p.sub(r' \1 ', text)
        return text

    @staticmethod
    def _handle_begin_sep(regexp, text):
        p = re.compile(r'^' + regexp, re.IGNORECASE)
        text = p.sub(r'\1 ', text)
        #         p = re.compile(r'[\A\b]' + regexp, re.IGNORECASE)
        #         text = p.sub(r'\1 ', text)
        p = re.compile(r'([^\w\b])' + regexp, re.IGNORECASE | re.UNICODE)
        text = p.sub(r'\1\2 ', text)
        p = re.compile("\s(-)", re.IGNORECASE)
        text = p.sub(r' \1 ', text)
        return text

    @staticmethod
    def _handle_end_sep(regexp, text):
        p = re.compile(regexp + r"([^\w/'`’´‘])", re.IGNORECASE | re.UNICODE)

        text = p.sub(r' \1\2', text)
        return text

    @staticmethod
    def _handle_sometimes_sep(text):
        p = re.compile(r'([\s\b][^/\s.\d\b:]+)(/+)([^/\s.\d\b]*[\b\s\./])', \
                       re.IGNORECASE | re.UNICODE)
        text = p.sub(r'\1  \2 \3', text)
        text = p.sub(r'\1  \2 \3', text)
        return text

    @staticmethod
    def _handle_middle_sep(regexp, text):
        p = re.compile(regexp, re.IGNORECASE | re.UNICODE)
        text = p.sub(r' \1 ', text)
        return text

    def _get_type(self, text):
        ab1_match = not self.ab1_re.match(text) is None
        ab2_match = not self.ab2_re.match(text) is None
        ab3_match = not self.ab3_re.match(text) is None
        url_match = not self.url_re.match(text) is None
        mail_match = not self.mail_re.match(text) is None
        num_match = not self.num_re.match(text) is None
        if num_match:
            return types['number']
        elif ab1_match or ab2_match or ab3_match:
            return types['abbreviation']
        elif url_match:
            return types['url']
        elif mail_match:
            return types['email']
        else:
            return types['word']


# ==============================================================================
class FileTokeniser:
    """ 
    Class which makes it possible to tokenise a whole txt file
    """

    def __init__(self, input_file, encoding):
        self.input_file = input_file
        self.encoding = encoding
        self.t = None
        self.tokeniser = RegExpTokeniser()

    def tokenise(self):
        """
        @deprecated: renamed as tokenise_file because FileTokeniser
                     is not a subclass of Tokeniser anymore
        """
        return self.tokenise_file()

    def tokenise_file(self):
        self.t = Text()
        try:
            f = codecs.open(self.input_file, 'r', self.encoding)
            lines = f.readlines()
            text = ''
            text = text.join(lines)
            self.t = self.tokeniser.tokenise(text)
            f.close()
        except IOError as e:
            raise TokeniserIOError(e)
        return self.t

    def write_result(self, of):
        try:
            f = codecs.open(self.input_file + '.tok', 'w', self.encoding)
            f.write(self._get_output(of))
            f.close()
        except IOError as e:
            raise TokeniserIOError(e)

    def _get_output(self, of):
        if of == 'space':
            return self.t.get_contents()
        elif of == 'xml':
            return self.t.to_XML()
        elif of == 'lines':
            return self.t.to_lines()
        return self.t.get_contents()


def print_usage():
    print("py_tokeniser_gsw.py [-f format] <encoding> <filename>")
    print(" + format is the output format:")
    print("    space - token1 token2 (default)")
    print("    xml   - <w>token</w>")
    print("    lines - token1 [NEWLINE] token2")
    print(" + encoding is the file encoding")
    print(" + filename is the name of the file to tokenise")


if __name__ == '__main__':
    output_format = "space"
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(0)
    else:
        k = 1
        print(sys.argv)
        if sys.argv[1] == '-f':
            output_format = sys.argv[2]
            k = 3
        ft = FileTokeniser(sys.argv[k + 1], sys.argv[k])
        try:
            ft.tokenise()
            ft.write_result(output_format)
        except TokeniserIOError as error:
            print("Tokeniser I/O error : %s" % (str(error)))
