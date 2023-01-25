#!/usr/bin/python3

import re, sys, copy, natives, argparse, json
from StreamReader import StreamReader
from Tokenizer import Tokenizer
from Environment import Environment
from Parser import Parser
from Helpers import evaluation, make_lambda
#sys.tracebacklimit=0

MAIN = {"args":[],"type":"call","func":{"const": False,"type":"var","value":"main"}}

def compile(code, fname):
	parser = Parser(Tokenizer(StreamReader(code)))
	ast = Parser(Tokenizer(StreamReader(code))).parse_toplevel()
	with open(fname + '.ast', 'w') as fin:
		fin.write(json.dumps(ast))

def execute(code, args):
	code = json.loads(code)
	globalenv = Environment()
	natives.setup_natives(globalenv)
	evaluation(code, globalenv)
	try:
		for el in args['args']:
			MAIN['args'].append({'type': 'str', 'value': args['args']})
	except:
		MAIN['args'].append({'type': 'null', 'value': None})
	evaluation(MAIN, globalenv)
		
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='The compiler for the --Name Pending-- language')
	parser.add_argument('code', help='The main file to run')
	parser.add_argument('--args', '-a', help='Arguments to pass to main as a list', nargs='*')
	args = vars(parser.parse_args())
	code = ""
	with open(args['code']) as fin:
		code = fin.read()
	ext = args['code'].split('.')
	if ext[1] == 'np':
		compile(code, ext[0])
	elif ext[1] == 'ast':
		execute(code, args)
	else:
		print('Input file not ".np" or ".ast"')
