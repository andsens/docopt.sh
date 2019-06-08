from .. import Function


class Value(Function):

  name = 'docopt_value'

  def __init__(self, settings):
    super(Value, self).__init__(settings, Value.name)

  @property
  def body(self):
    # $1=variable name
    # $2=option idx to find in the options list
    # $3=is it a list?
    body = '''
local i
for i in "${!docopt_left[@]}"; do
  local l=${docopt_left[$i]}
  if [[ ${docopt_parsed_params[$l]} = "$2" ]]; then
    docopt_left=("${docopt_left[@]:0:$i}" "${docopt_left[@]:((i+1))}")
    $docopt_testmatch && return 0
    local value
    value=$(printf -- "%q" "${docopt_parsed_values[$l]}")
    if [[ $3 = true ]]; then
      eval "$1+=($value)"
    else
      eval "$1=$value"
    fi
    return 0
  fi
done
return 1
'''
    return body
