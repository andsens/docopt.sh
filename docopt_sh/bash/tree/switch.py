from .. import Function


class Switch(Function):

  name = 'docopt_switch'

  def __init__(self, settings):
    super(Switch, self).__init__(settings, Switch.name)

  @property
  def body(self):
    # $1=variable name
    # $2=option idx to find in the options list
    # $3=should the value be incremented?
    body = '''
local i
for i in "${!docopt_left[@]}"; do
  local l=${docopt_left[$i]}
  if [[ ${docopt_parsed_params[$l]} = "$2" ]]; then
    docopt_left=("${docopt_left[@]:0:$i}" "${docopt_left[@]:((i+1))}")
    $docopt_testmatch && return 0
    if [[ $3 = true ]]; then
      eval "(($1++))"
    else
      eval "$1=true"
    fi
    return 0
  fi
done
return 1
'''
    return body
