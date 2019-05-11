

class Function(object):

  def __init__(self, settings, name):
    self.name = name
    self.settings = settings

  def include(self):
    return True

  def fn_wrap(self, script):
    return '{name}() {{\n{script}\n}}'.format(name=self.name, script=script.strip())
