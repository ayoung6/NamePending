from __future__ import print_function
import NamePending 

def setup_natives(env):
	natives = [
			{
			'name':'print',
			'func':(lambda x='':print(stringify(x), end=''))
			},
			{
			'name':'println',
			'func':(lambda x='':print(stringify(x), end='\n'))
			},
			{
			'name':'str',
			'func':(lambda x='':str(x))
			},
			{
			'name':'int',
			'func':(lambda x:int(x['value']))
			},
			{
			'name':'float',
			'func':(lambda x:float(x['value']))
			},
			{
			'name':'input',
			'func':(lambda x='':raw_input(x))
			}
		]

	for x in natives:
		env.define(x['name'], x['func'])
def convert(value):
	return {'string': value}
def stringify(value):
	if (type(value) != dict): return value;
	if value['type'] == 'list':
		a = []
		for x in value['value']:
			a.append(x['value'])
		return a
	elif value == None:
		return 'null'
	else:
		try:
			return value['value']
		except:
			return value
