from .. import Function


class Optional(Function):
  def __init__(self, settings):
    super(Optional, self).__init__(settings, 'optional')

  @property
  def body(self):
    body = '''
local pattern
for pattern in "$@"; do
  $pattern
done
return 0
'''
    return body
