from .. import Function


class OneOrMore(Function):
  def __init__(self, settings):
    super(OneOrMore, self).__init__(settings, '_do_oom')

  @property
  def body(self):
    # This entire $prev thing doesn't make sense.
    # I couldn't find a case anywhere, where we would match something
    # but not remove something from $_lft.
    body = '''
local i=0
local prev=${#_lft[@]}
while "_do$1"; do
  ((i++))
  [[ $prev -eq ${#_lft[@]} ]] && break
  prev=${#_lft[@]}
done
if [[ $i -ge 1 ]]; then
  return 0
fi
return 1
'''
    return body
