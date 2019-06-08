from .. import Function


class Either(Function):

  name = 'docopt_either'

  def __init__(self, settings):
    super(Either, self).__init__(settings, Either.name)

  @property
  def body(self):
    body = '''
local initial_left=("${docopt_left[@]}")
local best_match
local matched_count
local node
local unset_testmatch=true
$docopt_testmatch && unset_testmatch=false
docopt_testmatch=true
for node in "$@"; do
  if "$node"; then
    if [[ -z $matched_count || ${#docopt_left[@]} -lt $matched_count ]]; then
      best_match=$node
      matched_count=${#docopt_left[@]}
    fi
  fi
  docopt_left=("${initial_left[@]}")
done
$unset_testmatch && docopt_testmatch=false
if [[ -n $best_match ]]; then
  $best_match
  return 0
fi
docopt_left=("${initial_left[@]}")
return 1
'''
    return body
