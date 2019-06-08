from .. import Function


class Required(Function):

  name = 'docopt_required'

  def __init__(self, settings):
    super(Required, self).__init__(settings, Required.name)

  @property
  def body(self):
    body = '''
local initial_left=("${docopt_left[@]}")
local node
local unset_testmatch=true
$docopt_testmatch && unset_testmatch=false
docopt_testmatch=true
for node in "$@"; do
  if ! "$node"; then
    docopt_left=("${initial_left[@]}")
    $unset_testmatch && docopt_testmatch=false
    return 1
  fi
done
if $unset_testmatch; then
  docopt_testmatch=false
  docopt_left=("${initial_left[@]}")
  for node in "$@"; do
    "$node"
  done
fi
return 0
'''
    return body
