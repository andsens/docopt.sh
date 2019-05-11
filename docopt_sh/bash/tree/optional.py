from .. import Function


class Optional(Function):
  def __init__(self, settings):
    super(Optional, self).__init__(settings, 'optional')

  def __str__(self):
    script = '''
local pattern
for pattern in "$@"; do
  $pattern
done
return 0
'''
    return self.fn_wrap(script)
