from .. import Function


class Help(Function):
  def __init__(self, settings):
    super(Help, self).__init__(settings, 'help')

  def __str__(self):
    script = '''
printf -- "%s" "${docname}"
'''.format(docname=self.settings.script.doc.name)
    return self.fn_wrap(script)
