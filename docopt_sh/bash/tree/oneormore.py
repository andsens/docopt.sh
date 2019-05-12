from .. import Function


class OneOrMore(Function):
  def __init__(self, settings):
    super(OneOrMore, self).__init__(settings, 'oneormore')

  @property
  def body(self):
    # This entire $previous_left thing doesn't make sense.
    # I couldn't find a case anywhere, where we would match something
    # but not remove something from $left.
    body = '''
local times=0
local previous_left=${#left[@]}
while $1; do
  ((times++))
  [[ $previous_left -eq ${#left[@]} ]] && break
  previous_left=${#left[@]}
done
if [[ $times -ge 1 ]]; then
  return 0
fi
return 1
'''
    return body
