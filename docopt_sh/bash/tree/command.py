from .. import Function


class Command(Function):
  def __init__(self, settings):
    super(Command, self).__init__(settings, '_do_cmd')

  @property
  def body(self):
    # $1=variable name
    # $2=name of the command
    # $3=should the value be incremented?
    body = '''
local i
local name=${2:-$1}
for i in "${!_lft[@]}"; do
  local l=${_lft[$i]}
  if [[ ${_do_pp[$l]} = 'a' ]]; then
    if [[ ${_do_pv[$l]} != "$name" ]]; then
      return 1
    fi
    _lft=("${_lft[@]:0:$i}" "${_lft[@]:((i+1))}")
    $_do_tm && return 0
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
