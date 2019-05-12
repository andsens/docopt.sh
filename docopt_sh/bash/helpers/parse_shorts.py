from .. import Function


class ParseShorts(Function):

  def __init__(self, settings):
    super(ParseShorts, self).__init__(settings, '_do_shorts')

  @property
  def body(self):
    body = '''
local token=${_do_av[0]}
local value
_do_av=("${_do_av[@]:1}")
[[ $token = -* && $token != --* ]] || assert_fail
local remaining=${token#-}
while [[ -n $remaining ]]; do
  local short="-${remaining:0:1}"
  remaining="${remaining:1}"
  local i=0
  local similar=()
  local similar_idx=false
  for o in "${_do_sh[@]}"; do
    if [[ $o = "$short" ]]; then
      similar+=("$short")
      [[ $similar_idx = false ]] && similar_idx=$i
    fi
    ((i++))
  done
  if [[ ${#similar[@]} -gt 1 ]]; then
    _do_err "$(printf "%s is specified ambiguously %d times" "$short" "${#similar[@]}")"
  elif [[ ${#similar[@]} -lt 1 ]]; then
    similar_idx=${#_do_sh[@]}
    value=true
    _do_sh+=("$short")
    _do_lo+=('')
    _do_ac+=(0)
  else
    value=false
    if [[ ${_do_ac[$similar_idx]} -ne 0 ]]; then
      if [[ $remaining = '' ]]; then
        if [[ ${#_do_av[@]} -eq 0 || ${_do_av[0]} = '--' ]]; then
          _do_err "$(printf "%s requires argument" "$short")"
        fi
        value=${_do_av[0]}
        _do_av=("${_do_av[@]:1}")
      else
        value=$remaining
        remaining=''
      fi
    fi
    if [[ $value = false ]]; then
      value=true
    fi
  fi
  _do_pp+=("$similar_idx")
  _do_pv+=("$value")
done
'''
    return body
