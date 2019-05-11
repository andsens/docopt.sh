from .. import Function


class Either(Function):
  def __init__(self, settings):
    super(Either, self).__init__(settings, 'either')

  def __str__(self):
    script = '''
local initial_left=("${left[@]}")
local best_match
local previous_best
local pattern
local unset_test_match=true
$test_match && unset_test_match=false
test_match=true
for pattern in "$@"; do
  if $pattern; then
    if [[ -z $previous_best || ${#left[@]} -lt $previous_best ]]; then
      best_match=$pattern
      previous_best=${#left[@]}
    fi
  fi
  left=("${initial_left[@]}")
done
$unset_test_match && test_match=false
if [[ -n $best_match ]]; then
  $best_match
  return 0
fi
left=("${initial_left[@]}")
return 1
'''
    return self.fn_wrap(script)
