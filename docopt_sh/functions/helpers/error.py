from .. import Function


class Error(Function):
  def __init__(self, settings):
    super(Error, self).__init__(settings, 'error')

  def __str__(self):
    script = '''
printf "%s\\n" "$1"
exit 1
'''
    return self.fn_wrap(script)

