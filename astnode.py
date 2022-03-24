from typing import Any, Optional, List, TypeVar
import json

T = TypeVar("T", bound="ASTNode")

class ASTNode:

    IF: str = 'if'
    KW: str = 'kw'
    OP: str = 'op'
    VAR: str = 'var'
    NUM: str = 'num'
    DEC: str = 'dec'
    STR: str = 'str'
    LET: str = 'let'
    VARS: str = 'vars'
    ARGS: str = 'args'
    NULL: str = 'null'
    BOOL: str = 'bool'
    CALL: str = 'call'
    PUNC: str = 'punc'
    PROG: str = 'prog'
    FUNC: str = 'func'
    THEN: str = 'then'
    ELSE: str = 'else'
    LIST: str = 'list'
    NAME: str = 'name'
    BODY: str = 'body'
    LEFT: str = 'left'
    RIGHT: str = 'right'
    CONST: str = 'const'
    VALUE: str = 'value'
    IMPORT: str = 'import'
    RETURN: str = 'return'
    LAMBDA: str = 'lambda'
    BINARY: str = 'binary'
    ASSIGN: str = 'assign'
    VARDEF: str = 'vardef'
    VARNAME: str = 'varname'
    OPERATOR: str = 'operator'
    PROGLIST: str = 'progList'
    CONDITION: str = 'condition'
    LISTRETRIEVE: str = 'listretrieve'

    def __init__(self):
        self.typing: str = 'unknown'
        self.value: Any = None
        self.isconst: bool = False
        self.left: Optional[T] = None
        self.right: Optional[T] = None
        self.operator: Optional[str] = None
        self.func: Optional[T] = None
        self.args: Optional[List[T]] = None
        self.condition: Optional[T] = None
        self.then: Optional[T] = None
        self.eelse: Optional[T] = None
        self.name: Optional[str] = None
        self.vars: Optional[List[T]] = None
        self.body: Optional[T] = None
        self.progList: Optional[List[T]] = None
    
    def __str__(self) -> str:
        return json.dumps(ASTNode.json(self))

    @staticmethod
    def json(node: T) -> dict:
        # Unpack baseline object
        temp: dict = {
            key: (
                ASTNode.json(val)
                if type(val) == type(node)
                else val
            )
            for (key, val) in vars(node).items()
            if val is not None
        }

        # Unpack Opjects from Lists
        for (key, val) in temp.items():
            if type(val) == list:
                temp[key] = [ASTNode.json(x) for x in temp[key] if type(x) == type(node)]

        return temp

    @staticmethod
    def buildNode(node: dict) -> T:
        if type(node) in [None, ASTNode]:
            return node

        a = ASTNode # Shorthand reference
        temp: T = ASTNode()

        if 'typing' not in node.keys(): return temp

        typing: str = node['typing']

        if typing == a.IF:
            _condition: T = a.buildNode(node[a.CONDITION])
            _then: T = a.buildNode(node[a.THEN])
            _else: Optional[T] = a.buildNode(node[a.ELSE]) if a.ELSE in node.keys() else None

            temp.xif(_condition, _then).xelse(_else)
            
        elif typing == a.KW:
            temp.kw(node[a.VALUE])

        elif typing == a.OP:
            temp.op(node[a.VALUE])

        elif typing == a.VAR:
            temp.var(node[a.VALUE])

        elif typing == a.NUM:
            temp.num(node[a.VALUE])

        elif typing == a.DEC:
            temp.dec(node[a.VALUE])

        elif typing == a.STR:
            temp.str(node[a.VALUE])

        elif typing == a.LET:
            _func: T = a.buildNode(node[a.FUNC])
            _args: List[T] = [a.buildNode(x) for x in node[a.ARGS]]

            temp.call(_func, _args)

        elif typing == a.NULL:
            temp.null()

        elif typing == a.BOOL:
            temp.bool(node[a.VALUE])

        elif typing == a.CALL:
            _func: T = a.buildNode(node[a.FUNC])
            _args: List[T] = [a.buildNode(x) for x in node[a.ARGS]]

            temp.call(_func, _args)

        elif typing == a.PUNC:
            temp.punc(node[a.VALUE])

        elif typing == a.PROG:
            _progList: List[T] = [a.buildNode(x) for x in node[a.PROGLIST]]

            temp.prog(_progList)

        elif typing == a.LIST:
            _list: List[T] = [a.buildNode(x) for x in node[a.VALUE]]

            temp.list(_list)

        elif typing == a.IMPORT:
            temp.ximport(node[a.VALUE])

        elif typing == a.RETURN:
            _value: Optional[T] = node[a.VALUE] if a.VALUE in node.keys() else None

            temp.xreturn(node[a.VALUE])

        elif typing == a.LAMBDA:
            _name: str = node[a.NAME]
            _body: T = a.buildNode(node[a.BODY])
            _vars: List[T] = [a.buildNode(x) for x in node[a.VARS]]

            temp.xlambda(_name, _vars, _body)

        elif typing == a.BINARY:
            _operator: str = node[a.OPERATOR]
            _left: T = a.buildNode(node[a.LEFT])
            _right: T = a.buildNode(node[a.RIGHT])

            temp.binary(_operator, _left, _right)

        elif typing == a.ASSIGN:
            _operator: str = node[a.OPERATOR]
            _left: T = node[a.LEFT]
            _right: T = node[a.RIGHT] if a.RIGHT in node.keys() else ASTNode().null()

            temp.assign(_operator, _left, _right)

        elif typing == a.LISTRETRIEVE:
            _name: str = node[a.NAME]
            _value: list = node[a.VALUE]

            temp.listRetrieve(_name, _value)

        elif typing == a.VARNAME:
            _value: str = node[a.VALUE]
            
            temp.varname(_value)

        else:
            raise Exception(f'Can\'t unpack {node}')

        if a.CONST in node.keys() and node[a.CONST]: temp.const()

        return temp

    def const(self, const: bool = True) -> T:
        self.isconst = const
        return self

    def varname(self, name: str) -> T:
        self.typing = ASTNode.VARNAME
        self.value = name
        return self

    def vardef(self, name: str, vars: T) -> T:
        self.typing = ASTNode.vardef
        self.value = name
        self.vars = vars
        return self

    def function(self, function: Optional[str] = None, args: Optional[list] = None) -> T:
        self.typing = ASTNode.CALL
        self.func = function
        self.args = args
        return self

    def binary(self, operator: str, left: T, right: T) -> T:
        self.typing = ASTNode.BINARY
        return self.__binary_assign(operator, left, right)

    def assign(self, operator: str, left: T, right: T) -> T:
        self.typing = ASTNode.ASSIGN
        return self.__binary_assign(operator, left, right)

    def __binary_assign(self, operator: str, left: T, right: T) -> T:
        self.operator = operator
        self.left = left
        self.right = right
        return self

    def call(self, func: T, args: List[T]) -> T:
        self.typing = ASTNode.CALL
        self.func = func
        self.args = args
        return self

    def ximport(self, value: str) -> T:
        self.typing = ASTNode.IMPORT
        self.value = value
        return self

    def xlambda(self, name: str, vars: List[T], body: T) -> T:
        self.typing = ASTNode.LAMBDA
        self.name = name
        self.vars = vars
        self.body = body
        return self

    def xif(self, condition: T, then: T) -> T:
        self.typing = ASTNode.IF
        self.condition = condition
        self.then = then
        return self

    def xelse(self, xelse: Optional[T]) -> T:
        if xelse is not None and self.typing is ASTNode.IF and (self.condition and self.then):
            self.eelse = xelse
        return self

    def null(self) -> T:
        self.typing = ASTNode.NULL
        self.value = self.typing
        return self

    def var(self, value: Optional[str] = None) -> T:
        self.typing = ASTNode.VAR
        self.value = value
        return self

    def prog(self, progList: List[T]) -> T:
        self.typing = ASTNode.PROG
        self.progList = progList
        return self

    def list(self, value: List[T] = []) -> T:
        self.typing = ASTNode.LIST
        self.value = value
        return self

    def listRetrieve(self, name: str, value: list) -> T:
        self.typing = ASTNode.LISTRETRIEVE
        self.name = name
        self.value = value

    def xreturn(self, value: Optional[T] = None) -> T:
        self.typing = ASTNode.RETURN
        self.value = value
        return self

    def xbool(self, value: Optional[bool] = None) -> T:
        self.typing = ASTNode.BOOL
        self.value = value
        return self

    def kw(self, value: Optional[str] = None) -> T:
        self.typing = ASTNode.KW
        self.value = value
        return self

    def num(self, value: Optional[int] = None) -> T:
        self.typing = ASTNode.NUM
        self.value = value
        return self

    def dec(self, value: Optional[float] = None) -> T:
        self.typing = ASTNode.DEC
        self.value = value
        return self

    def str(self, value: Optional[str] = None) -> T:
        self.typing = ASTNode.STR
        self.value = value
        return self

    def punc(self, value: Optional[str] = None) -> T:
        self.typing = ASTNode.PUNC
        self.value = value
        return self

    def op(self, value: Optional[str] = None) -> T:
        self.typing = ASTNode.OP
        self.value = value
        return self