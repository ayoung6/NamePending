from typing import Optional, Any, TypeVar
from astnode import ASTNode
from streamreader import StreamReader

T = TypeVar('T', bound='Environment')

class Environment:
    def __init__(self, parent: Optional[T] = None):
        self.parent: Optional[T] = parent
        self.vars: dict = {}
        self.const: list = []
        self.importList: list = []

        if parent:
            self.vars.update(parent.vars)
            for x in parent.const: self.const.append(x)
            for x in parent.importList: self.importList.append(x)

    def extend(self) -> T:
        return Environment(self)

    def addImport(self, name: str) -> None:
        self.importList.append(name)

    def hasImport(self, name: str) -> bool:
        return name in self.importList

    def lookup(self, name: str) -> T:
        scope: T = self

        # Dig through current and parent scopes for var lookups
        while scope:
            if name in scope.vars:
                return scope

            scope = scope.parent

    def get(self, name: str) -> Any:
        if name in self.vars:
            return self.vars[name]

        StreamReader.error(f'Undefined Variable: {name}')

    def set(self, name: str, value: ASTNode, const: bool = False) -> ASTNode:
        scope: T = self.lookup(name)
        
        if name in self.const:
            raise Exception(f'Cannot Assign to "const" Variable: {name}')

        if scope: # Var reassignment
            scope.vars[name] = value
            if const:
                scope.const.append(name)
            return scope.vars[name]
        else: # Var assignment
            self.vars[name] = value
            if const:
                self.const.append(name)
            return self.vars[name]

    def define(self, name: str, value, const: bool = False) -> None:
        if name in self.vars:
            self.set(name, value, const)
        else:
            self.vars.update({name:value})
            if const:
                self.const.append(name)
