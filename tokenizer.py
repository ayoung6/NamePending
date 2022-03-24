from astnode import ASTNode
from streamreader import StreamReader
from typing import Optional, List, Callable

import re

class Tokenizer():
    CURRENT: Optional[ASTNode] = None
    KEY_WORDS: List[str] = [
        'import',
        'const',
        'return',
        'let',
        'if',
        'then',
        'else',
        'lambda',
        'λ',
        'true',
        'false',
        'null',
    ]

    def __init__(self, streamReader: StreamReader):
        self.stream: StreamReader = streamReader

    def isInt(self, char: str) -> bool:
        return re.search('^\d$', char)

    def isIdStart(self, char: str) -> bool:
        return re.search('^[a-zA-Zλ_]$', char)

    def isPunctuation(self, char: str) -> bool:
        return '[]{}(),;'.find(char) >= 0

    def isOperation(self, char: str) -> bool:
        return '+-*/%=&|<>!'.find(char) >= 0

    def isId(self, char: str) -> bool:
        return self.isIdStart(char) or '?!-<>=0123456789'.find(char) >= 0

    def isKeyword(self, string: str) -> bool:
        return string in Tokenizer.KEY_WORDS

    def readWhile(self, conditional: Callable) -> str:
        string: str = ''
        while not self.stream.eof() and conditional(self.stream.peek()):
            string += self.stream.next()
        return string

    def readEscaped(self, end: str) -> str:
        escaped: bool = False
        string: str = ''
        self.stream.next()
        while not self.stream.eof():
            char: str = self.stream.next()
            if escaped:
                string += char
                escaped = False
            elif char == end:
                break
            else:
                string += char
        return string

    def tokenizeString(self, end: str) -> ASTNode:
        return ASTNode().str(self.readEscaped(end))

    def tokenizeNumber(self) -> ASTNode:
        hasDot: bool = False
        string: str = ''
        while not self.stream.eof():
            char = self.stream.peek()
            if char == '.':
                if hasDot:
                    break
                else:
                    hasDot = True
                    string += self.stream.next()
                    continue
            if not self.isInt(char):
                break
            else:
                string += self.stream.next()
        if hasDot:
            return ASTNode().dec(float(string))
        else:
            return ASTNode().num(int(string))

    def tokenizeIdentifier(self, const: bool = False) -> ASTNode:
        identity: str = self.readWhile(self.isId)
        if identity == ASTNode.CONST:
            while self.stream.peek().isspace():
                self.stream.next()
            return self.tokenizeIdentifier(True)

        if self.isKeyword(identity):
            return ASTNode().kw(identity).const(const)
        else:
            return ASTNode().var(identity).const(const)

    def tokenize(self) -> Optional[ASTNode]:
        while not self.stream.eof() and self.stream.peek().isspace():
            self.stream.next()

        if self.stream.eof(): return None

        char: str = self.stream.peek()

        if char == '#':
            self.stream.skipComment()
            return self.next()

        if char in ['"', "'"]:
            return self.tokenizeString(
                '"' if char == '"' else "'"
            )

        if self.isInt(char): return self.tokenizeNumber()
        if self.isIdStart(char): return self.tokenizeIdentifier()
        if self.isPunctuation(char):
            return ASTNode().punc(self.stream.next())
        if self.isOperation(char):
            return ASTNode().op(self.readWhile(self.isOperation))

        StreamReader.error(f'{char} is not a recognized character')

    def peek(self) -> Optional[ASTNode]:
        if not Tokenizer.CURRENT:
            Tokenizer.CURRENT = self.tokenize()
        return Tokenizer.CURRENT

    def next(self) -> ASTNode:
        tok: Optional[ASTNode] = Tokenizer.CURRENT
        Tokenizer.CURRENT = None
        return tok if tok else self.tokenize()

    def eof(self) -> bool:
        return self.peek() is None