from .. import Function


class Optional(Function):
  def __init__(self, settings):
    super(Optional, self).__init__(settings, '_do_opt')

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
