import re

class Tokenizer:
    CURRENT = None
    KEY_WORDS = ['import', 'const', 'return', 'let', 'if', 'then', 'else', 'lambda', 'λ', 'true', 'false', 'null']

    def __init__(self, streamReader):
        self.stream = streamReader
        self.int_pattern = re.compile(r'^\d$')
        self.id_start_pattern = re.compile(r'^[a-zA-Zλ_]$')
        self.punctuation = "[]{}(),;"
        self.operations = "+-*/%=&|<>!"
        self.id_chars = "?!-<>=0123456789"

    def is_int(self, char):
        return self.int_pattern.search(char) is not None

    def is_id_start(self, char):
        return self.id_start_pattern.search(char) is not None

    def is_punctuation(self, char):
        return self.punctuation.find(char) >= 0

    def is_operation(self, char):
        return self.operations.find(char) >= 0

    def is_id(self, char):
        return self.is_id_start(char) or self.id_chars.find(char) >= 0

    def is_keyword(self, string):
        return string in Tokenizer.KEY_WORDS

    def read_while(self, conditional):
        string = ""
        while not self.stream.eof() and conditional(self.stream.peek()):
            string += self.stream.next()
        return string

    def read_escaped(self, end):
        escaped = False
        string = ''
        self.stream.next()
        while not self.stream.eof():
            char = self.stream.next()
            if escaped:
                string += char
                escaped = False
            elif char == end:
                break
            else:
                string += char
        return string

    def tokenize_string(self, end):
        return {"type": "str", "value": self.read_escaped(end)}

    def tokenize_number(self):
        has_dot = False
        string = ""
        while not self.stream.eof():
            char = self.stream.peek()
            if char == '.':
                if has_dot:
                    break
                else:
                    has_dot = True
                    string += self.stream.next()
                    continue
            if not self.is_int(char):
                break 
            else:
                string += self.stream.next()
        if has_dot:
            return {'type': 'num', 'value': float(string)}
        else:
            return {'type': 'num', 'value': int(string)}
            
    def tokenize_identifier(self, const=False):
        identity = self.read_while(self.is_id)
        if identity == 'const':
            while self.stream.peek().isspace():
                self.stream.next()
            return self.tokenize_identifier(True)
        return {'type': 'kw' if self.is_keyword(identity) else 'var',
            'value': identity,
            'const': const}

    def tokenize(self):
        while self.stream.peek().isspace():
            self.stream.next()
        if self.stream.eof():return False
        char = self.stream.peek()
        if char == '#':
            self.stream.skipComment()
            return self.next()
        if char == '"':return self.tokenize_string('"')
        if char == "'":return self.tokenize_string("'")
        if self.is_int(char):return self.tokenize_number()
        if self.is_id_start(char):return self.tokenize_identifier()
        if self.is_punctuation(char):
            return {'type': 'punc', 'value': self.stream.next()}
        if self.is_operation(char):
            return {'type': 'op', 'value': self.read_while(self.is_operation)}
    
        self.stream.error('%s is not a recognized character \n' % char)

    def peek(self):
        if not Tokenizer.CURRENT:
            Tokenizer.CURRENT = self.tokenize()
        return Tokenizer.CURRENT

    def next(self):
        tok = Tokenizer.CURRENT
        Tokenizer.CURRENT = None
        return tok if tok else self.tokenize()

    def eof(self):
        return self.peek() == False