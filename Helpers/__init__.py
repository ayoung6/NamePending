import copy
from Parser import Parser
from Tokenizer import Tokenizer
from StreamReader import StreamReader

def evaluation(exp, env):
	exptype = exp['type']
	if exptype == 'import':
		if env.has_import(exp['file']):return
		env.add_import(exp['file'])
		code = ''
		with open(exp['file']) as fin:
			code = fin.read()
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
			a = copy.deepcopy(values)
			for x in exp['left']['value']:	
				try:
					a['value'][x['value']] = env.get(exp['right']['value'])
				except:
					a['value'][x['value']] = evaluation(exp['right'], env)
			env.set(exp['left']['name'], a)
			return a
		StreamReader.error("Cannot assign to %s" % exp['left'])
	elif exptype == 'list_retreve':
		if len(exp['value']) == 1:
			var_name = exp['name']
			index = evaluation(exp['value'][0], env)
			stored_value = env.get(var_name)
			if (stored_value['type'] == 'list'):
				return evaluation(stored_value['value'][index['value']], env)
			return(stored_value)
		elif len(exp['value']) > 1:
			lst = []
			var = env.get(exp['name'])
			for x in exp['value']:
				x = evaluation(x, env)
				lst.append(var[x['value']])
			return lst
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
			if var['type'] == 'return':
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
	elif op == '&&': return build('bool', a != False and b)
	elif op == '||': return build('bool', a if a != False else b)
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
                for i in range(0, len(names)):
                        scope.define(names[i]['name'], args[i], names[i]['const'])
                return evaluation(exp['body'], scope)
	if exp['name']:
		name = exp['name']
		env = env.extend()
		env.define(name, lamda)
	return lamda