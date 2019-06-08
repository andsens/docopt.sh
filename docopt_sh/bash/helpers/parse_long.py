from .. import Function


class ParseLong(Function):

  def __init__(self, settings):
    super(ParseLong, self).__init__(settings, 'docopt_parse_long')

  @property
  def body(self):
    body = '''
local token=${docopt_argv[0]}
local long=${token%%=*}
local value=${token#*=}
local argcount
docopt_argv=("${docopt_argv[@]:1}")
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
for o in "${docopt_longs[@]}"; do
  if [[ $o = "$long" ]]; then
    similar+=("$long")
    [[ $match = false ]] && match=$i
  fi
  ((i++))
done
if [[ $match = false ]]; then
  i=0
  for o in "${docopt_longs[@]}"; do
    if [[ $o = $long* ]]; then
      similar+=("$long")
      [[ $match = false ]] && match=$i
    fi
    ((i++))
  done
fi
if [[ ${#similar[@]} -gt 1 ]]; then
  docopt_error "$(printf "%s is not a unique prefix: %s?" \\
    "$long" "${similar[*]}")"
elif [[ ${#similar[@]} -lt 1 ]]; then
  [[ $eq = '=' ]] && argcount=1 || argcount=0
  match=${#docopt_shorts[@]}
  [[ $argcount -eq 0 ]] && value=true
  docopt_shorts+=('')
  docopt_longs+=("$long")
  docopt_argcount+=("$argcount")
else
  if [[ ${docopt_argcount[$match]} -eq 0 ]]; then
    if [[ $value != false ]]; then
      docopt_error "$(printf "%s must not have an argument" \\
        "${docopt_longs[$match]}")"
    fi
  elif [[ $value = false ]]; then
    if [[ ${#docopt_argv[@]} -eq 0 || ${docopt_argv[0]} = '--' ]]; then
      docopt_error "$(printf "%s requires argument" "$long")"
    fi
    value=${docopt_argv[0]}
    docopt_argv=("${docopt_argv[@]:1}")
  fi
  if [[ $value = false ]]; then
    value=true
  fi
fi
docopt_parsed_params+=("$match")
docopt_parsed_values+=("$value")
'''
    return body
