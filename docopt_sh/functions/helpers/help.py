from .. import Function


class Help(Function):
  def __init__(self, docname):
    super(Help, self).__init__('help')
    self.docname = docname

  def __str__(self):
    script = '''
printf -- "%s" "${docname}"
'''.format(docname=self.docname)
    return self.fn_wrap(script)
