from .. import Function


class Optional(Function):

  name = '_do_opt'

  def __init__(self, settings):
    super(Optional, self).__init__(settings, Optional.name)

  @property
  def body(self):
    body = '''
local p
for p in "$@"; do
  "_do$p"
done
return 0
'''
    return body
