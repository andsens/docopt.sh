from .. import Function


class OneOrMore(Function):
  def __init__(self, settings):
    super(OneOrMore, self).__init__(settings, 'oneormore')

  def __str__(self):
    script = '''
local times=0
# shellcheck disable=SC2154
local previous_left=${#left[@]}
while $1; do
  ((times++))
  if [[ $previous_left -eq ${#left[@]} ]]; then
    # This entire $previous_left thing doesn't make sense.
    # I couldn't find a case anywhere, where we would match something
    # but not remove something from $left.
    break
  fi
  previous_left=${#left[@]}
done
if [[ $times -ge 1 ]]; then
  return 0
fi
return 1
'''
    return self.fn_wrap(script)
