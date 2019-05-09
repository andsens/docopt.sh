

class Function(object):

  def __init__(self, name):
    self.name = name

  def include(self):
    return True

  def fn_wrap(self, script):
    return '{name}() {{ {script}; }}'.format(name=self.name, script=script.strip())
