from .. import Function


class ParseShorts(Function):

  def __init__(self, settings):
    super(ParseShorts, self).__init__(settings, 'docopt_parse_shorts')

  @property
  def body(self):
    body = '''
local token=${docopt_argv[0]}
local value
docopt_argv=("${docopt_argv[@]:1}")
[[ $token = -* && $token != --* ]] || assert_fail
local rem=${token#-}
while [[ -n $rem ]]; do
  local short="-${rem:0:1}"
  rem="${rem:1}"
  local i=0
  local similar=()
  local match=false
  for o in "${docopt_shorts[@]}"; do
    if [[ $o = "$short" ]]; then
      similar+=("$short")
      [[ $match = false ]] && match=$i
    fi
    ((i++))
  done
  if [[ ${#similar[@]} -gt 1 ]]; then
    docopt_error "$(printf "%s is specified ambiguously %d times" \\
      "$short" "${#similar[@]}")"
  elif [[ ${#similar[@]} -lt 1 ]]; then
    match=${#docopt_shorts[@]}
    value=true
    docopt_shorts+=("$short")
    docopt_longs+=('')
    docopt_argcount+=(0)
  else
    value=false
    if [[ ${docopt_argcount[$match]} -ne 0 ]]; then
      if [[ $rem = '' ]]; then
        if [[ ${#docopt_argv[@]} -eq 0 || ${docopt_argv[0]} = '--' ]]; then
          docopt_error "$(printf "%s requires argument" "$short")"
        fi
        value=${docopt_argv[0]}
        docopt_argv=("${docopt_argv[@]:1}")
      else
        value=$rem
        rem=''
      fi
    fi
    if [[ $value = false ]]; then
      value=true
    fi
  fi
  docopt_parsed_params+=("$match")
  docopt_parsed_values+=("$value")
done
'''
    return body
