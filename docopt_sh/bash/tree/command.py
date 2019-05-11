from .. import Function


class Command(Function):
  def __init__(self, settings):
    super(Command, self).__init__(settings, '_command')

  def __str__(self):
    # $1=variable name
    # $2=should the value be incremented?
    # $3=name of the command
    script = '''
local i
for i in "${!left[@]}"; do
  local l=${left[$i]}
  if [[ ${parsed_params[$l]} == 'a' ]]; then
    if [[ ${parsed_values[$l]} != "$3" ]]; then
      return 1
    fi
    left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
    $test_match && return 0
    if [[ $2 == true ]]; then
      eval "(($1++))"
    else
      eval "$1=true"
    fi
    return 0
  fi
done
return 1
'''
    return self.fn_wrap(script)
