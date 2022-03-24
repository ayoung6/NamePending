from typing import TypeVar

T = TypeVar("T", bound="StreamReader")

class StreamReader:
    instance: T

    def __init__(self, stream: str, infile: str):
        self.stream: str = stream
        self.pos: int = 0
        self.line: int = 1 
        self.col: int = 1
        self.infile: str = infile
        StreamReader.instance = self
    
    def next(self) -> str:
        char: str = self.peek()
        
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char

    def peek(self) -> str:
        return self.stream[self.pos] if self.pos < len(self.stream) else None

    def skipComment(self) -> None:
        line: int = self.line
        while self.line == line:
            self.next()

    def eof(self) -> bool:
        return self.peek() is None

    @staticmethod
    def error(errmsg: str) -> None:
        raise Exception(f"({StreamReader.instance.infile}) {errmsg} at location : Line({StreamReader.instance.line}) Char({StreamReader.instance.col})")