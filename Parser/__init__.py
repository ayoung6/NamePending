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