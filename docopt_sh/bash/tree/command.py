from .. import Function


class Command(Function):

  name = 'docopt_command'

  def __init__(self, settings):
    super(Command, self).__init__(settings, Command.name)

  @property
  def body(self):
    # $1=variable name
    # $2=name of the command
    # $3=should the value be incremented?
    body = '''
local i
local name=${2:-$1}
for i in "${!docopt_left[@]}"; do
  local l=${docopt_left[$i]}
  if [[ ${docopt_parsed_params[$l]} = 'a' ]]; then
    if [[ ${docopt_parsed_values[$l]} != "$name" ]]; then
      return 1
    fi
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
