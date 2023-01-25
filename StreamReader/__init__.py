class StreamReader:
    def __init__(self, stream):
        self.stream = stream
        self.pos = 0
        self.line = 1
        self.col = 1

    def next(self):
        char = self.peek()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char

    def peek(self):
        return self.stream[self.pos] if self.pos < len(self.stream) else ''

    def skipComment(self):
        while self.stream[self.pos] != '\n':
            self.next()

    def eof(self):
        return self.peek() == ''

    def error(self, errmsg):
        raise Exception("%s at location line:%d column:%d" % (errmsg, self.line, self.col))
