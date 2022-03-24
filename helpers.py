import json

from typing import Callable, Optional, List, Any
import typing
from astnode import ASTNode
from environment import Environment

from parse import Parser
from tokenizer import Tokenizer
from streamreader import StreamReader


opperationFunctions: dict = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x / y,
    '%': lambda x, y: x % y,
    '<': lambda x, y: x < y,
    '>': lambda x, y: x > y,
    '<=': lambda x, y: x <= y,
    '>=': lambda x, y: x >= y,
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x != y,
    '&&': lambda x, y: x and y,
    '||': lambda x, y: x or y,
}

def applyOp(opperation: str, left: ASTNode, right: ASTNode) -> ASTNode:
    if left.typing == ASTNode.LIST:
        if len(left.value) == 0:
            return ASTNode().list([ASTNode().null() * right.value])
        
        return ASTNode().list([left.value * right.value])

    try:
        ast: ASTNode = ASTNode()
        _value: Any = opperationFunctions[opperation](left.value, right.value)
        _typing: str = ASTNode.BOOL if type(_value) == bool else left.typing
        
        ast.typing = _typing
        ast.value = _value
        
        return ast

    except:
        StreamReader.error(f"Cannot apply Opperator {opperation}")

def makeLambda(node: ASTNode, env: Environment) -> Callable:
    def func(*args):
        names: List[ASTNode] = node.vars
        scope: Environment = env.extend()

        for i in range(len(names)):
            scope.define(
                names[i].name,
                args[i],
                names[i].const
                )

        if node.body == False: return
        return evaluation(node.body, scope)

    if node.name:
        name: str = node.name
        env = env.extend()
        env.define(name, func)

    return func

def evaluation(node: ASTNode, env: Environment) -> Optional[ASTNode]:
    typing: str = node.typing
    if typing == ASTNode.PROG:
        for var in node.progList:
            val: ASTNode = evaluation(var, env)
            if var.typing == ASTNode.RETURN:
                return val

        return ASTNode().null()

    elif typing == ASTNode.IMPORT:
        if env.hasImport(node.value): return

        contents: str = ''
        ast: Optional[ASTNode]

        try:
            with open(node.value + '.ast', encoding='utf-8') as fin: contents = fin.read()
            ast = ASTNode.buildNode(contents)

        except:
            with open(node.value + '.np', encoding='utf-8') as fin: contents = fin.read()
            ast = Parser(Tokenizer(StreamReader(contents, node.value))).parseTopLevel()

        env.addImport(node.value)
        evaluation(ast, env)

    elif typing in (ASTNode.NUM, ASTNode.DEC, ASTNode.BOOL, ASTNode.STR, ASTNode.NULL):
        return node

    elif typing == ASTNode.ASSIGN:
        _left: ASTNode = ASTNode.buildNode(node.left)
        _right: ASTNode = ASTNode.buildNode(node.right)
        
        if _left.typing == ASTNode.VAR:
            return env.set(
                _left.value,
                evaluation(_right, env),
                _left.const
                )

        elif _left.value == ASTNode.LISTRETRIEVE:
            values: ASTNode = env.get(_left.name)
            for x in _left.value:
                try:
                    values.value[x.value] = env.get(_right.value)
                
                except:
                    values.value[x.value] = evaluation(_right, env)

            env.set(_left.name, values)
            return values
        StreamReader.error(f'Cannot assign to {_left.name}')

    elif typing == ASTNode.LISTRETRIEVE:
        if len(node.value) == 1:
            index: ASTNode = evaluation(node.value[0], env)
            return evaluation(env.get(node.name), env).value[index.value]

        elif len(node.value) > 1:
            lst: list = []
            var: ASTNode = env.get(node.name)
            for x in node.value:
                x = evaluation(x, env)
                lst.append(var.value[x.value])

            return ASTNode().list(lst)

    elif typing == ASTNode.VAR:
        print(node)
        val: ASTNode = env.get(node.value)

        try:
            return evaluation(env.get(node.value), env)

        except:
            return env.get(node.value)

    elif typing == ASTNode.BINARY:
        return applyOp(node.operator, evaluation(node.left, env), evaluation(node.right, env))
    
    elif typing == ASTNode.LAMBDA:
        return makeLambda(node, env)

    elif typing == ASTNode.RETURN:
        returnVal: ASTNode
        try:
            returnVal = env.get(node.value)

        except:
            returnVal = evaluation(node.value, env)

        if returnVal.typing == ASTNode.LIST:
            lst: List[ASTNode] = []

            for x in range(len(returnVal.value)):
                lst.append(evaluation(returnVal.value[x], env))

            return ASTNode().list(lst)

        return returnVal

    elif typing == ASTNode.LIST:
        return node

    elif typing == ASTNode.LET:
        scope: Environment = env.extend()

        for x in node.vars:
            scope.define(
                x.name,
                evaluation(x.vars, env) if x.vars else False,
                x.const
                )

        return evaluation(node.body, scope)

    elif typing == ASTNode.IF:
        cond: ASTNode = evaluation(node.condition, env)

        if not cond.value: return evaluation(node.then, env)

        try:
            return evaluation(node.xelse, env)

        except:
            return False

    elif typing == ASTNode.CALL:
        func: Callable = evaluation(node.func, env)
        params: List[ASTNode] = [evaluation(x, env) for x in node.args]

        return func(*params)

    else:
        StreamReader.error(f'Cannot Evaluate Type {typing} : {ASTNode.json(node)}')