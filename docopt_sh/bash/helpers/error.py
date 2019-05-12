from .. import Function


class Error(Function):
  def __init__(self, settings, usage_section):
    super(Error, self).__init__(settings, '_do_err')
    self.usage_start, self.usage_end = usage_section
    if self.settings.script.doc.value.endswith('\n'):
      self.usage_end -= 1

  @property
  def body(self):
    body = '''
[[ -n $1 ]] && printf "%s\\n" "$1"
printf "%s\\n" "${{{docname}:{start}:{length}}}"
exit 1
'''.format(
      docname=self.settings.script.doc.name,
      start=self.usage_start,
      length=self.usage_end - self.usage_start,
    )
    return body
