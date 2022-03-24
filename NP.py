import argparse
import natives
import json

from typing import TYPE_CHECKING
from parse import Parser
from streamreader import StreamReader
from tokenizer import Tokenizer
from environment import Environment
from helpers import evaluation
    
from astnode import ASTNode

def compile(code: str, fname: str) -> None:
    # parser: Parser = Parser(Tokenizer(StreamReader(code)))
    # ^ left in as a reminder that i made 2 ASTs before the rewrite

    ast: ASTNode = Parser(Tokenizer(StreamReader(code, fname))).parseTopLevel()

    with open(fname + '.ast', mode='w', encoding='utf-8') as fout:
        fout.write(json.dumps(ast, default=ASTNode.json, separators=(',', ':')))

def execute(code: str, args: dict) -> None:
    code: ASTNode = ASTNode.buildNode(json.loads(code))
    globalEnv: Environment = Environment()
    natives.setupNatives(globalEnv)

    # Commandline arguments are globally available
    globalEnv.define('arglength', ASTNode().num(0))
    globalEnv.define('arglist', ASTNode().null())

    if args['args'] != None:
        globalEnv.define('arglength', ASTNode().num(len(args['args'])))
        globalEnv.define('arglist', ASTNode().list(
                [
                    ASTNode().str(x) for x in args['args']
                ]
            )
        )
    evaluation(code, globalEnv)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='The compiler for the --Name Pending-- language')
    parser.add_argument('code', help='The main file to run')
    parser.add_argument('--run', '-r', help='Runs from a ".np" file', action='store_true')
    parser.add_argument('--args', '-a', help='Arguments to pass to main as a list', nargs='*')
    args: dict = vars(parser.parse_args())

    code: str = ""

    with open(args['code'], encoding='utf-8') as fin:
        code = fin.read()

    ext: list[str] = args['code'].split('.')

    if ext[1] == 'np':
        compile(code, ext[0])

        if args['run']:
            with open(ext[0] + '.ast', encoding='utf-8') as fin:
                code = fin.read()

            execute(code, args)

    elif ext[1] == 'ast':
        execute(code, args)

    else:
        print('Invalid input file, expecting ".np" or ".ast"')
        
