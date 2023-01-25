from collections import defaultdict

class Environment(object):
    def __init__(self, parent=None):
        self.vars = defaultdict(lambda: None)
        self.const = set()
        self.importlist = set()
        if parent:
            self.vars.update(parent.vars)
            self.const.update(parent.const)
            self.importlist.update(parent.importlist)
        self.parent = parent
    def extend(self):
        return Environment(self)
    def add_import(self, name):
        self.importlist.add(name)
    def has_import(self, name):
        return name in self.importlist
    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        raise Exception("Undefined Variable: %s" % name)
    def set(self, name, value, const=False):
        if name in self.const:
            raise Exception('Cannot assign to const variable %s' % name)
        self.vars[name] = value
        if const:
            self.const.add(name)
        return self.vars[name]
    def define(self, name, value, const=False):
        if const:
            self.const.add(name)
        self.vars[name] = value
