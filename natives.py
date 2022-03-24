
def setupNatives(env):
    natives = [
        {
            'name': 'print',
            'func':(lambda x: print(x.value if x else '', end=''))
        },
        {
            'name': 'println',
            'func': (lambda x: print(x.value if x else '', end='\n'))
        }
    ]

    for native in natives:
        env.define(native['name'], native['func'])