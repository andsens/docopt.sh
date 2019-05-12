from .. import Function


class Value(Function):
  def __init__(self, settings):
    super(Value, self).__init__(settings, '_do_val')

  @property
  def body(self):
    # $1=variable name
    # $2=option idx to find in the options list
    # $3=is it a list?
    body = '''
local i
for i in "${!_lft[@]}"; do
  local l=${_lft[$i]}
  if [[ ${_do_pp[$l]} = "$2" ]]; then
    _lft=("${_lft[@]:0:$i}" "${_lft[@]:((i+1))}")
    $_do_tm && return 0
    local value
    value=$(printf -- "%q" "${_do_pv[$l]}")
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
