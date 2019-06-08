from .. import Function


class Optional(Function):

  name = 'docopt_optional'

  def __init__(self, settings):
    super(Optional, self).__init__(settings, Optional.name)

  @property
  def body(self):
    body = '''
local node
for node in "$@"; do
  "$node"
done
return 0
'''
    return body
