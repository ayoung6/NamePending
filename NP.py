#!/usr/bin/python
#-*- encoding=utf-8 -*-

from __future__ import print_function
import re, sys, copy, natives, argparse, json
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')
#sys.tracebacklimit=0

MAIN = {"args":[],"type":"call","func":{"const": False,"type":"var","value":"main"}}

class StreamReader(object):
	line = 0
	col = 0
	def __init__(self, stream):
		self.stream = stream
		self.pos = 0
	def next(self):
		char = self.peek()
		self.pos += 1
		if char == '\n':
			StreamReader.line += 1
			StreamReader.col = 0
		else:
			StreamReader.col += 1
		return char
	def peek(self):
		return self.stream[self.pos] if self.pos < len(self.stream) else ''
	def skipComment(self):
		line = StreamReader.line
		while StreamReader.line == line:
			self.next()
	def eof(self):
		return self.peek() == ''
	@staticmethod
	def error(errmsg):
		raise Exception("%s at location line:%d column:%d" %(errmsg, StreamReader.line, StreamReader.col))

class Tokenizer(object):
	CURRENT = None
	KEY_WORDS = ['import', 'const', 'return', 'let', 'if', 'then', 'else', 'lambda', 'λ', 'true', 'false', 'null']

	def __init__(self, streamReader):
		self.stream = streamReader
	def is_int(self, char):
		return re.search('^\d$', char)
	def is_id_start(self, char):
		return re.search('^[a-zA-Zλ_]$', char)
	def is_punctuation(self, char):
		return "[]{}(),;".find(char) >= 0
	def is_operation(self, char):
		return "+-*/%=&|<>!".find(char) >= 0
	def is_id(self, char):
		return self.is_id_start(char) or "?!-<>=0123456789".find(char) >= 0
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
		if char is '#':
			self.stream.skipComment()
			return self.next()
		if char is '"':return self.tokenize_string('"')
		if char is "'":return self.tokenize_string("'")
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
class Parser(object):
	PRECEDENCE = {'=': 1, '||': 2, '&&': 3,
			'<': 7, '>': 7, '<=': 7, '>=': 7, '==': 7, '!=': 7,
			'+': 10, '-': 10, '*': 20, '/': 20, '%': 20}
	def __init__(self, tokenizer):
		self.tokenizer = tokenizer
	def is_punc(self, punc = None):
		token = self.tokenizer.peek()
		return token and token['type'] == 'punc' and (not punc or token['value'] == punc) and token
	def is_kw(self, kw = None):
		token = self.tokenizer.peek()
		return token and token['type'] == 'kw' and (not kw or token['value'] == kw) and token
	def is_op(self, op = None):
		token = self.tokenizer.peek()
		return token and token['type'] == 'op' and (not op or token['value'] == op) and token
	def skip_punc(self, punc):
		if self.is_punc(punc): self.tokenizer.next()
		else: self.tokenizer.stream.error('Expecting Punctuation: "%s"' % punc)
	def skip_op(self, op):
		if self.is_op(op): self.tokenizer.next()
		else: self.tokenizer.stream.error('Expecting Operator: "%s"' % op)
	def skip_kw(self, kw):
		if self.is_kw(kw): self.tokenizer.next()
		else: self.tokenizer.stream.error('Expecting Keyword: "%s"' % kw)
	def unexpected(self, token):
		self.tokenizer.stream.error('Unexpected Token %r' % token)
	def maybe_binary(self, left, my_pred):
		token = self.is_op()
		if token:
			his_prec = Parser.PRECEDENCE[token['value']]
			if his_prec > my_pred:
				self.tokenizer.next()
				right = self.maybe_binary(self.parse_atom(), his_prec)
				binary = {
					'type': 'assign' if token['value'] == '=' else 'binary',
					'operator': token['value'],
					'left': left,
					'right': right
					}
				return self.maybe_binary(binary, my_pred)
		return left
	def delimited(self, start, stop, separator, parser):
		a = []
		first = True
		self.skip_punc(start)
		while not self.tokenizer.eof():
			if self.is_punc(stop): break
			if first: first = False
			else: self.skip_punc(separator)
			if self.is_punc(stop): break
			a.append(parser())
		self.skip_punc(stop)
		return a
	def parse_call(self, function):
		return {
			'type': 'call',
			'func': function,
			'args': self.delimited('(', ')', ',', self.parse_expression)
			}
	def parse_varname(self):
		name = self.tokenizer.next()
		if name['type'] != 'var': self.tokenizer.stream.error("Expected Variable Name")
		return {'name':name['value'], 'const':name['const']}
	def parse_if(self):
		self.skip_kw('if')
		cond = self.parse_expression()
		if not self.is_punc('{'): self.skip_kw('then')
		then = self.parse_expression()
		ret = {
			'type': 'if',
			'cond': cond,
			'then': then
			}
		if self.is_kw('else'):
			self.tokenizer.next()
			ret.update({'else': self.parse_expression()})
		return ret
	def parse_lambda(self):
		return {
			'type': 'lambda',
			'name': self.tokenizer.next()['value'] if self.tokenizer.peek()['type'] == 'var' else False,
			'vars': self.delimited('(', ')', ',', self.parse_varname),
			'body': self.parse_expression()
			}
	def parse_vardef(self):
		name = self.parse_varname()
		var = ''
		if self.is_op('='):
			self.tokenizer.next()
			var = self.parse_expression()
		return {'name': name, 'def': var}
	def parse_let(self):
		self.skip_kw('let')
		if self.tokenizer.peek()['type'] == 'var':
			name = self.tokenizer.next()['value']	
			defs = self.delimited('(', ')', ',', self.parse_vardef)
			getname = lambda x: x['name']
			def getval(x): 
				try:return x['def'] 
				except:return False
			defines = [getname(x) for x in defs]
			values = [getval(x) for x in defs]
			return {
				'type': 'call',
				'func': {
					'type': 'lambda',
					'name': name,
					'vars': defines,
					'body': self.parse_expression()
					},
				'args': values
				}
		return {
			'type': 'let',
			'vars': self.delimited('(', ')', ',', self.parse_vardef),
			'body': self.parse_expression()
			}
	def parse_bool(self):
		return {
			'type': 'bool',
			'value': self.tokenizer.next()['value'] == 'true'
			}
	def maybe_call(self, expr=None):
		expr = expr()
		return self.parse_call(expr) if self.is_punc('(') else expr
	def parse_return(self):
		self.tokenizer.next()
                return {
                        'type':'return',
                        'value':self.parse_expression()
                        }
	def parse_list(self):
		return {
			'type':'list',
			'value':self.delimited('[', ']', ',', self.parse_expression)
			}
	def parse_import(self):
		self.skip_kw('import')
		return {
			'type':'import',
			'file':self.tokenizer.next()['value']
			}
	def _parse_atom_func(self):	
		if self.is_punc('('):
			self.tokenizer.next()
			exp = self.parse_expression()
			self.skip_punc(')')
			return exp
		if self.is_punc('{'): return self.parse_prog()
		if self.is_punc('['): return self.parse_list()
		if self.is_kw('return'): return self.parse_return()
		if self.is_kw('let'): return self.parse_let()
		if self.is_kw('if'): return self.parse_if()
		if self.is_kw('import'):return self.parse_import()
		if self.is_kw('null'): 
			self.skip_kw('null')
			return {'type': 'null', 'value': 'null'}
		if self.is_kw('true') or self.is_kw('false'): return self.parse_bool()
		if self.is_kw('lambda') or self.is_kw('λ'): 
			self.tokenizer.next()
			return self.parse_lambda()
		token = self.tokenizer.next()
		if token:
			ttype = token['type']
			if ttype == 'var':
				if self.is_punc('['):
                                        return {
                                                'type':'list_retreve',
                                                'name':token['value'],
                                                'value': self.delimited('[', ']', ',', self.parse_expression)
                                                }
                                return token
			if ttype == 'num' or ttype == 'str':
				return token
			self.unexpected(token)
	def parse_atom(self):
		return self.maybe_call(self._parse_atom_func)
	def parse_toplevel(self):
		prog = []
		while not self.tokenizer.eof():
			prog.append(self.parse_expression())
			if not self.tokenizer.eof(): self.skip_punc(';')
		return {
			'type': 'prog',
			'prog': prog
			}
	def parse_prog(self):
		prog = self.delimited('{', '}', ';', self.parse_expression)
		if len(prog) == 0: return False
		if len(prog) == 1: return prog[0]
		return {
			'type': 'prog',
			'prog': prog
			}
	def parse_expression(self):
		return self.maybe_call(lambda mb = self.maybe_binary, pa = self.parse_atom: mb(pa(), 0))
class Environment(object):
	def __init__(self, parent=None):
		self.var = {}
		self.const = []
		self.importlist = []
		if parent:
			self.var.update(parent.var)
			for x in parent.const:self.const.append(x)
			for x in parent.importlist:self.importlist.append(x)
		self.parent = parent
	def extend(self):
		return Environment(self)
	def add_import(self, name):
		self.importlist.append(name)
	def has_import(self, name):
		return name in self.importlist
	def lookup(self, name):
		scope = self
		while scope:
			if name in scope.var:
				return scope
			scope = scope.parent
	def get(self, name):
		if name in self.var:
			return self.var[name]
		StreamReader.error("Undefined Variable: %s" % name)
	def set(self, name, value, const=False):
		scope = self.lookup(name)
		if name in self.const:
			raise Exception('Cannot assign to const variable %s' % name)
		if scope:
			scope.var[name] = value
			if const:
                                self.const.append(name)
			return scope.var[name]
		else:
			self.var[name] = value
			if const:
				self.const.append(name)
			return self.var[name]
	def define(self, name, value, const=False):
		if name in self.var:
			self.set(name, value, const)
		else:
			self.var.update({name:value})
			if const:
				self.const.append(name)
def evaluation(exp, env):
	exptype = exp['type']
	if exptype == 'import':
		if env.has_import(exp['file']):return
		env.add_import(exp['file'])
		code = ''
		with open(exp['file']) as fin:
			code = fin.read()
		parser = Parser(Tokenizer(StreamReader(code)))
	        ast = Parser(Tokenizer(StreamReader(code))).parse_toplevel()
		evaluation(ast, env)
        elif exptype in ('num', 'str', 'bool', 'null'):
		return exp
	elif exptype == 'assign':
		if exp['left']['type'] == 'var':
			return env.set(exp['left']['value'], evaluation(exp['right'], env), exp['left']['const'])
		elif exp['left']['type'] == 'list_retreve':
			lastVal = None
			values = env.get(exp['left']['name'])	
			#a = copy.deepcopy(values)
			for x in exp['left']['value']:	
				try:
					values['value'][x['value']] = env.get(exp['right']['value'])
				except:
					values['value'][x['value']] = evaluation(exp['right'], env)
			env.set(exp['left']['name'], values)
			return values
		StreamReader.error("Cannot assign to %s" % exp['left'])
	elif exptype == 'list_retreve':
		if len(exp['value']) == 1:
                        index = evaluation(exp['value'][0], env)
                        return evaluation(env.get(exp['name']), env)['value'][index['value']]
		elif len(exp['value']) > 1:
			lst = []
			var = env.get(exp['name'])
			for x in exp['value']:
				x = evaluation(x, env)
				lst.append(var['value'][x['value']])
                        return {'type': 'list', 'value': lst}
	elif exptype == 'var':
		try:
                	return evaluation(env.get(exp['value']), env)
		except:
			return env.get(exp['value'])
	elif exptype == 'binary':
		return apply_op(exp['operator'], evaluation(exp['left'], env), evaluation(exp['right'], env))
	elif exptype == 'lambda':
		return make_lambda(env, exp)
	elif exptype == 'return':
		returnval = ''
		try:
			returnval = env.get(exp['value'])
		except:
			returnval = evaluation(exp['value'], env)
		if returnval['type'] == 'list':
			a = []
			for x in range(len(returnval['value'])):
				a.append(evaluation(returnval['value'][x], env))
			return {'type': 'list', 'value': a}
		return returnval
	elif exptype == 'list':
		return exp
	elif exptype == 'let':
		scope = env.extend()
		for x in exp['vars']:
			scope.define(x['name']['name'], evaluation(x['def'], env) if x['def'] else False, x['name']['const'])
		return evaluation(exp['body'], scope)
	elif exptype == 'if':
		cond = evaluation(exp['cond'], env)
		if cond['value'] != False: return evaluation(exp['then'], env)
		try:
			return evaluation(exp['else'], env)
		except:
			return False
	elif exptype == 'prog':
		val = False
		for var in exp['prog']:
			val = evaluation(var, env)
			if (var['type'] == 'return'):
                                return val
		return None
	elif exptype == 'call':
		func = evaluation(exp['func'], env)
		params = [evaluation(x, env) for x in exp['args']]
		return func(*params)
	else:
		StreamReader.error("Cannot Evaluate Type %s" % exptype)
def apply_op(op, a, b):
	def build(t, val):
		return {'type': t, 'value': val}
	def num(x):
		try:
			x = x['value']
		except:
			pass
		if isinstance(x, (int, long)) or isinstance(x, float):
			return x
		raise Exception('%s is not a number' % x)
        def boolean(x):
                try:
                        x = x['value']
                except:
                        pass
                if isinstance(x, bool):
                        return x
                raise Exception('%s is not a boolean' % x)
	def div(x):
		try:
			x = x['value']
		except:
			pass
		if num(x) == 0: 
			StreamReader.error('Cannot divide by zero') 
		else: return x
	if a['type'] == 'list' and op == '*':
		if len(a['value']) == 0:
			return {'type': 'list', 'value': [{'type': 'null', 'value': 'null'}]*num(b)}
		return {'type': 'list', 'value': a['value']*num(b)}
	if op == '+' : return build('num', num(a) + num(b))
	elif op == '-' : return build('num', num(a) - num(b))
	elif op == '*' : return build('num', num(a) * num(b))
	elif op == '/' : return build('num', num(a) / div(b))
	elif op == '%' : return build('num', num(a) % div(b))
	elif op == '&&': return build('bool', boolean(a) != False and boolean(b))
	elif op == '||': return build('bool', boolean(a) if boolean(a) != False else boolean(b))
	elif op == '<' : return build('bool', num(a) < num(b))
	elif op == '>' : return build('bool', num(a) > num(b))
	elif op == '<=': return build('bool', num(a) <= num(b))
	elif op == '>=': return build('bool', num(a) >= num(b))
	elif op == '==': return build('bool', a == b)
	elif op == '!=': return build('bool', a != b)
	StreamReader.error("Cannot apply aperator %s" % op)
def make_lambda(env, exp):
	def lamda(*args):
                names = exp['vars']	
                scope = env.extend()
                for i in xrange(0, len(names)):
                        scope.define(names[i]['name'], args[i], names[i]['const'])
                if(exp['body'] == False): return
                return evaluation(exp['body'], scope)
	if exp['name']:
		name = exp['name']
		env = env.extend()
		env.define(name, lamda)
	return lamda

def compile(code, fname):
	parser = Parser(Tokenizer(StreamReader(code)))
	ast = Parser(Tokenizer(StreamReader(code))).parse_toplevel()
	with open(fname + '.ast', 'w') as fin:
		fin.write(json.dumps(ast))

def execute(code, args):
        length = 0
	code = json.loads(code)
	globalenv = Environment()
	natives.setup_natives(globalenv)
	evaluation(code, globalenv)
	try:
                final_args = {'type': 'list', 'value': []};
		for el in args['args']:
		        final_args['value'].append({'type': 'str', 'value': el})	
                MAIN['args'].append(final_args)
                length = len(args['args'])
	except:
		MAIN['args'].append({'type': 'null', 'value': 'null'})
        MAIN['args'].append({'type': 'num', 'value': length})
	evaluation(MAIN, globalenv)
		
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='The compiler for the --Name Pending-- language')
	parser.add_argument('code', help='The main file to run')
        parser.add_argument('--run', '-r', help='Runs from a ".np" file', action='store_true')
	parser.add_argument('--args', '-a', help='Arguments to pass to main as a list', nargs='*')
	args = vars(parser.parse_args())
	code = ""
	with open(args['code']) as fin:
		code = fin.read()
	ext = args['code'].split('.')
        if ext[1] == 'np' and args['run']:
                compile(code, ext[0])
                with open(ext[0] + '.ast') as fin:
                        code = fin.read()
                execute(code, args)
	elif ext[1] == 'np':
		compile(code, ext[0])
	elif ext[1] == 'ast':
		execute(code, args)
	else:
		print('Input file not ".np" or ".ast"')
