from .. import Function


class ParseShorts(Function):

  def __init__(self, settings):
    super(ParseShorts, self).__init__(settings, 'parse_shorts')

  def __str__(self):
    script = '''
token=${argv[0]}
argv=("${argv[@]:1}")
[[ $token == -* && $token != --* ]] || assert_fail
local remaining=${token#-}
while [[ -n $remaining ]]; do
  short="-${remaining:0:1}"
  remaining="${remaining:1}"
  local i=0
  local similar=()
  local similar_idx=false
  for o in "${options_short[@]}"; do
    if [[ $o == "$short" ]]; then
      similar+=("$short")
      [[ $similar_idx == false ]] && similar_idx=$i
    fi
    ((i++))
  done
  if [[ ${#similar[@]} -gt 1 ]]; then
    error "$(printf "%s is specified ambiguously %d times" "$short" "${#similar[@]}")"
  elif [[ ${#similar[@]} -lt 1 ]]; then
    similar_idx=${#options_short[@]}
    value=true
    options_short+=("$short")
    options_long+=('')
    options_argcount+=(0)
  else
    value=false
    if [[ ${options_argcount[$similar_idx]} -ne 0 ]]; then
      if [[ $remaining == '' ]]; then
        if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
          error "$(printf "%s requires argument" "$short")"
        fi
        value=${argv[0]}
        argv=("${argv[@]:1}")
      else
        value=$remaining
        remaining=''
      fi
    fi
    if [[ $value == false ]]; then
      value=true
    fi
  fi
  parsed_params+=("$similar_idx")
  parsed_values+=("$value")
done
'''
    return self.fn_wrap(script)
