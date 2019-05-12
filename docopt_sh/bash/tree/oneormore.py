from .. import Function


class OneOrMore(Function):
  def __init__(self, settings):
    super(OneOrMore, self).__init__(settings, 'oneormore')

  @property
  def body(self):
    # This entire $prev_lft thing doesn't make sense.
    # I couldn't find a case anywhere, where we would match something
    # but not remove something from $_lft.
    body = '''
local times=0
local prev_lft=${#_lft[@]}
while $1; do
  ((times++))
  [[ $prev_lft -eq ${#_lft[@]} ]] && break
  prev_lft=${#_lft[@]}
done
if [[ $times -ge 1 ]]; then
  return 0
fi
return 1
'''
    return body
