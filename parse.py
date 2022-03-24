from typing import Callable, Optional, Any, List
from tokenizer import Tokenizer
from astnode import ASTNode

class Parser:
    PRECEDENCE = {
        '=': 1, '||': 2, '&&': 3,
        '<': 7, '>': 7, '<=': 7, '>=': 7, '==': 7, '!=': 7,
        '+': 10, '-': 10, '*': 20, '/': 20, '%': 20
	}

    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer: Tokenizer = tokenizer

    def __error(self, errmsg: str) -> None:
        self.tokenizer.stream.error(errmsg, self.tokenizer.stream)

    def __checkTok(self, token: ASTNode, checkVal: str, x: Optional[str] = None) -> ASTNode:
        return (
            token
            and token.typing == checkVal
            and (not x or token.value == x)
            and token
        )

    def peek(self) -> ASTNode:
        return self.tokenizer.peek()

    def isPunc(self, punc: Optional[str] = None) -> ASTNode:
        return self.__checkTok(self.peek(), ASTNode.PUNC, punc)

    def isKw(self, kw: Optional[str] = None) -> ASTNode:
        return self.__checkTok(self.peek(), ASTNode.KW, kw)

    def isOp(self, op: Optional[str] = None) -> ASTNode:
        return self.__checkTok(self.peek(), ASTNode.OP, op)

    def skipPunc(self, punc: str) -> None:
        if self.isPunc(punc):
            self.tokenizer.next()
        else:
            self.__error(f'Expecting Punctuation: "{punc}"')

    def skipOp(self, op: str) -> None:
        if self.isOp(op):
            self.tokenizer.next()
        else:
            self.__error(f'Expecting Operator: "{op}"')

    def skipKw(self, kw: str) -> None:
        if self.isKw(kw):
            self.tokenizer.next()
        else:
            self.__error(f'Expecting Keyword: "{kw}"')

    def unexpected(self, token: Any) -> None:
        self.__error(f'Unexpected Token: "{token}"')

    def maybeBinary(self, left: ASTNode, myPred: int) -> ASTNode:
        token: ASTNode = self.isOp()
        binary: Optional[ASTNode] = None
        if token:
            hisPred = Parser.PRECEDENCE[token.value]
            if hisPred > myPred:
                self.tokenizer.next()
                right: ASTNode = self.maybeBinary(self.parseAtom(), hisPred)
                if token.value == '=':
                    binary = ASTNode().assign(token.value, left, right)
                else:
                    binary = ASTNode().binary(token.value, left, right)
                return self.maybeBinary(binary, myPred)
        return left

    def delimited(self, start: str, stop: str, separator: str, parser: Callable) -> List[ASTNode]:
        a: List[ASTNode] = []
        first: bool = True
        self.skipPunc(start)

        while not self.tokenizer.eof():
            if self.isPunc(stop): break

            if first:
                first = False
            else:
                self.skipPunc(separator)

            if self.isPunc(stop): break
            
            a.append(parser())
            
        self.skipPunc(stop)
        return a

    def parseCall(self, func: str) -> ASTNode:
        return ASTNode().function(func, self.delimited('(', ')', ',', self.parseExpression))

    def parseIf(self) -> ASTNode:
        self.skipKw(ASTNode.IF)
        cond: ASTNode = self.parseExpression()

        if not self.isPunc('{'): self.skipKw(ASTNode.THEN)

        then: ASTNode = self.parseExpression()

        ifNode: ASTNode = ASTNode().xif(cond, then)

        if self.isKw(ASTNode.ELSE):
            self.tokenizer.next()
            ifNode.xelse(self.parseExpression())

        return ifNode

    def parseLambda(self) -> ASTNode:
        return ASTNode().xlambda(
            self.tokenizer.next().value if self.tokenizer.peek().typing == ASTNode.VAR else False,
            self.delimited('(', ')', ',', self.parseVarnames),
            self.parseExpression()
        )

    def parseVarnames(self) -> dict:
        node: ASTNode = self.tokenizer.next()
        isconst: bool = node.isconst

        if node.typing != ASTNode.VAR:
            self.__error("Expected Variable Name")
            
        node = ASTNode().var(node.value)
        return node.const() if isconst else node

    def parseVardef(self) -> dict:
        name: dict = self.parseVarnames()
        var: ASTNode

        if self.isOp('='):
            self.tokenizer.next()
            var = self.parseExpression()
            
        # TODO: Replace dict with object
        # return {'name': name, 'def': var}
        return ASTNode().vardef(name, var)

    def parseLet(self) -> ASTNode:
        self.skipKw(ASTNode.LET)

        if self.tokenizer.peek().typing == ASTNode.VAR:
            name: str = self.tokenizer.next().value
            defs: List[ASTNode] = self.delimited('(', ')', ',', self.parseVardef)
            getName: Callable = lambda x: x.value

            def getVal(x):
                try: return x.defs
                except: return False

            defines: list = [getName(x) for x in defs]
            values: list = [getVal(x) for x in defs]

            return ASTNode().call(
                ASTNode().xlambda(
                    name,
                    defines,
                    self.parseExpression()
                ),
                values
            )

    def parseBool(self) -> ASTNode:
        return ASTNode().xbool(self.tokenizer.next().value == 'true')

    def maybeCall(self, expr: Optional[Callable] = None) -> ASTNode:
        expr = expr()
        return self.parseCall(expr) if self.isPunc('(') else expr

    def parseReturn(self) -> ASTNode:
        self.tokenizer.next()
        return ASTNode().xreturn(self.parseExpression())

    def parseImport(self) -> ASTNode:
        self.skipKw(ASTNode.IMPORT)
        return ASTNode().ximport(self.tokenizer.next().value)

    def parseList(self) -> ASTNode:
        return ASTNode().list(self.delimited('[', ']', ',', self.parseExpression))

    def _parseAtomFunction(self) -> Optional[ASTNode]:
        if self.isPunc('('):
            self.tokenizer.next()
            exp: ASTNode = self.parseExpression()
            self.skipPunc(')')
            return exp

        if self.isPunc('{'): return self.parseProg()

        if self.isPunc('['): return self.parseList()

        if self.isKw(ASTNode.RETURN): return self.parseReturn()

        if self.isKw(ASTNode.LET): return self.parseLet()

        if self.isKw(ASTNode.IF): return self.parseIf()

        if self.isKw(ASTNode.IMPORT): return self.parseImport()

        if self.isKw(ASTNode.NULL):
            self.skipKw(ASTNode.NULL)
            return ASTNode().null()

        if self.isKw('true') or self.isKw('false'): return self.parseBool()

        if self.isKw(ASTNode.LAMBDA) or self.isKw('λ'):
            self.tokenizer.next()
            return self.parseLambda()
        
        token: Optional[ASTNode] = self.tokenizer.next()

        if token:
            ttype: str = token.typing
            
            if ttype == ASTNode.VAR:
                if self.isPunc('['): # Accessing a list, so we return from list storage
                    return ASTNode().listRetrieve(
                        token.value,
                        self.delimited('[', ']', ',', self.parseExpression)
                    )
                return token # Not a list, return raw variable data

            if ttype in [ASTNode.NUM, ASTNode.DEC, ASTNode.STR]:
                return token
            
            # All cases checked by here, anything else is unknown
            self.unexpected(token)

        # TODO: Dont know what to do here, check at some point

    def parseAtom(self) -> ASTNode:
        return self.maybeCall(self._parseAtomFunction)

    def parseTopLevel(self) -> ASTNode:
        progList: List[ASTNode] = []

        while not self.tokenizer.eof():
            progList.append(self.parseExpression())

            if not self.tokenizer.eof(): self.skipPunc(';')

        return ASTNode().prog(progList)

    def parseProg(self) -> ASTNode:
        prog: list = self.delimited('{', '}', ';', self.parseExpression)

        if len(prog) == 0: return False
        if len(prog) == 1: return prog[0]

        return ASTNode().prog(prog)

    def parseExpression(self) -> ASTNode:
        return self.maybeCall(
            lambda mb = self.maybeBinary, pa = self.parseAtom: mb(pa(), 0)
        )