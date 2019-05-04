#!/usr/bin/env bash

parse_shorts() {
# def parse_shorts(tokens, options):
# """shorts ::= '-' ( chars )* [ [ ' ' ] chars ] ;"""
  token=${argv[0]}
  argv=("${argv[@]:1}")
# token = tokens.move()
  [[ $token == -* && $token != --* ]] || assert_fail
# assert token.startswith('-') and not token.startswith('--')
  local left=${token#-}
# left = token.lstrip('-')
# parsed = []
  while [[ -n $left ]]; do
# while left != '':
    short="-${left:0:1}"
    left="${left:1}"
#   short, left = '-' + left[0], left[1:]
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
#   similar = [o for o in options if o.short == short]
    if [[ ${#similar[@]} -gt 1 ]]; then
#   if len(similar) > 1:
      die "%s is specified ambiguously %d times" "$short" "${#similar[@]}"
#     raise tokens.error('%s is specified ambiguously %d times' %
#              (short, len(similar)))
    elif [[ ${#similar[@]} -lt 1 ]]; then
#   elif len(similar) < 1:
#     o = Option(short, None, 0)
#     options.append(o)
      similar_idx=${#options_short[@]}
      value=(true)
      options_short+=("$short")
      options_long+=('')
      options_argcount+=(0)
      options_value+=(false)
#     if tokens.error is DocoptExit:
#       o = Option(short, None, 0, True)
    # Moved before appending to options
    else
#   else:  # why copying is necessary here?
#     o = Option(short, similar[0].long,
#          similar[0].argcount, similar[0].value)
      value=false
#     value = None
      if [[ ${options_argcount[$similar_idx]} -ne 0 ]]; then
#     if o.argcount != 0:
        if [[ $left == '' ]]; then
#       if left == '':
          if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
#         if tokens.current() in [None, '--']:
            die "%s requires argument" "$short"
#           raise tokens.error('%s requires argument' % short)
          fi
          value=${argv[0]}
          argv=("${argv[@]:1}")
#         value = tokens.move()
        else
#       else:
          value=$left
#         value = left
          left=''
#         left = ''
        fi
      fi
#     if tokens.error is DocoptExit:
      if [[ $value == false ]]; then
#       o.value = value if value is not None else True
        value=true
      fi
    fi
    parsed_params+=("$similar_idx")
    parsed_values+=("$value")
#   parsed.append(o)
  done
# return parsed
}
