from .. import Function


class ParseLong(Function):

  def __init__(self, settings):
    super(ParseLong, self).__init__(settings, '_do_long')

  @property
  def body(self):
    body = '''
local token=${_do_av[0]}
local long=${token%%=*}
local value=${token#*=}
local argcount
_do_av=("${_do_av[@]:1}")
[[ $token = --* ]] || assert_fail
if [[ $token = *=* ]]; then
  eq='='
else
  eq=''
  value=false
fi
local i=0
local similar=()
local match=false
for o in "${_do_lo[@]}"; do
  if [[ $o = "$long" ]]; then
    similar+=("$long")
    [[ $match = false ]] && match=$i
  fi
  ((i++))
done
if [[ $match = false ]]; then
  i=0
  for o in "${_do_lo[@]}"; do
    if [[ $o = $long* ]]; then
      similar+=("$long")
      [[ $match = false ]] && match=$i
    fi
    ((i++))
  done
fi
if [[ ${#similar[@]} -gt 1 ]]; then
  _do_err "$(printf "%s is not a unique prefix: %s?" \
    "$long" "${similar[*]}")"
elif [[ ${#similar[@]} -lt 1 ]]; then
  [[ $eq = '=' ]] && argcount=1 || argcount=0
  match=${#_do_sh[@]}
  [[ $argcount -eq 0 ]] && value=true
  _do_sh+=('')
  _do_lo+=("$long")
  _do_ac+=("$argcount")
else
  if [[ ${_do_ac[$match]} -eq 0 ]]; then
    if [[ $value != false ]]; then
      _do_err "$(printf "%s must not have an argument" \
        "${_do_lo[$match]}")"
    fi
  elif [[ $value = false ]]; then
    if [[ ${#_do_av[@]} -eq 0 || ${_do_av[0]} = '--' ]]; then
      _do_err "$(printf "%s requires argument" "$long")"
    fi
    value=${_do_av[0]}
    _do_av=("${_do_av[@]:1}")
  fi
  if [[ $value = false ]]; then
    value=true
  fi
fi
_do_pp+=("$match")
_do_pv+=("$value")
'''
    return body
