from .. import Function


class Help(Function):
  def __init__(self, settings):
    super(Help, self).__init__(settings, 'help')
    if self.settings.script.doc.value.endswith('\n'):
      self.printf_template = "%s"
    else:
      self.printf_template = "%s\\n"

  @property
  def body(self):
    body = '''
printf -- "{template}" "${docname}"
'''.format(
      template=self.printf_template,
      docname=self.settings.script.doc.name,
    )
    return body
