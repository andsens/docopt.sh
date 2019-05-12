from .. import Function


class Switch(Function):
  def __init__(self, settings):
    super(Switch, self).__init__(settings, '_do_sw')

  @property
  def body(self):
    # $1=variable name
    # $2=option idx to find in the options list
    # $3=should the value be incremented?
    body = '''
local i
for i in "${!_lft[@]}"; do
  local l=${_lft[$i]}
  if [[ ${_do_pp[$l]} = "$2" ]]; then
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
