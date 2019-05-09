from .. import Function


class Error(Function):
  def __init__(self):
    super(Error, self).__init__('error')

  def __str__(self):
    script = '''
printf "%s\\n" "$1"
exit 1
'''
    return self.fn_wrap(script)

