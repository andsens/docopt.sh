#!/usr/bin/env bash

parse_long() {
# def parse_long(tokens, options):
# """long ::= '--' chars [ ( ' ' | '=' ) chars ] ;"""
  token=${argv[0]}
  long=${token%%=*}
  value=${token#*=}
  argv=("${argv[@]:1}")
# long, eq, value = tokens.move().partition('=')
# assert long.startswith('--')
  [[ $token == --* ]] || assert_fail
  if [[ $token = *=* ]]; then
    eq='='
  else
    eq=''
    value=false
  fi
# value = None if eq == value == '' else value
  local i=0
  local similar=()
  local similar_idx=false
  for o in "${options_long[@]}"; do
    if [[ $o == "$long" ]]; then
      similar+=("$long")
      [[ $similar_idx == false ]] && similar_idx=$i
    fi
    ((i++))
  done
# similar = [o for o in options if o.long == long]
  if [[ ${#similar[@]} -eq 0 ]]; then
# if tokens.error is DocoptExit and similar == []:  # if no exact match
    for o in "${options_long[@]}"; do
      if [[ $o == $long* ]]; then
        similar+=("$long")
        [[ $similar_idx == false ]] && similar_idx=$i
      fi
      ((i++))
    done
#   similar = [o for o in options if o.long and o.long.startswith(long)]
  fi
  if [[ ${#similar[@]} -gt 1 ]]; then
# if len(similar) > 1:  # might be simply specified ambiguously 2+ times?
    die "%s is not a unique prefix: %s?" "$long" "${similar[*]}"
#   raise tokens.error('%s is not a unique prefix: %s?' %
#            (long, ', '.join(o.long for o in similar)))
  elif [[ ${#similar[@]} -lt 1 ]]; then
# elif len(similar) < 1:
    if [[ $eq == '=' ]]; then
      argcount=1
    else
      argcount=0
    fi
#   argcount = 1 if eq == '=' else 0
#   o = Option(None, long, argcount)
    similar_idx=${#options_short[@]}
    if [[ argcount -eq 0 ]]; then
      value=true
    fi
    options_short+=('')
    options_long+=("$long")
    options_argcount+=("$argcount")
#   options.append(o)
#   if tokens.error is DocoptExit:
#     o = Option(None, long, argcount, value if argcount else True)
    # Moved before appending to options
  else
# else:
#   o = Option(similar[0].short, similar[0].long,
#        similar[0].argcount, similar[0].value)
    if [[ ${options_argcount[$similar_idx]} -eq 0 ]]; then
#   if o.argcount == 0:
      if [[ $value != false ]]; then
#     if value is not None:
        die "%s must not have an argument" "$long"
#       raise tokens.error('%s must not have an argument' % o.long)
      fi
    else
#   else:
      if [[ $value == false ]]; then
#     if value is None:
        if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
#       if tokens.current() in [None, '--']:
          die "%s requires argument" "$long"
#         raise tokens.error('%s requires argument' % o.long)
        fi
#       value = tokens.move()
        value=${argv[0]}
        argv=("${argv[@]:1}")
      fi
    fi
#   if tokens.error is DocoptExit:
    if [[ $value == false ]]; then
      value=true
#     o.value = value if value is not None else True
    fi
  fi
  parsed_params+=("$similar_idx")
  parsed_values+=("$value")
# return [o]
}
