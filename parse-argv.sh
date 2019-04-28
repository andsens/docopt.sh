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
    options_short+=('')
    options_long+=("$long")
    options_argcount+=("$argcount")
    options_value+=(false)
#   options.append(o)
#   if tokens.error is DocoptExit:
#     o = Option(None, long, argcount, value if argcount else True)
    parsed_options_short+=('')
    parsed_options_long+=("$long")
    parsed_options_argcount+=("$argcount")
    if [[ argcount -eq 0 ]]; then
      parsed_options_value+=("$value")
    else
      parsed_options_value+=(true)
    fi
    parsed_types+=('o')
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
  parsed_options_short+=("${options_short[$similar_idx]}")
  parsed_options_long+=("${options_long[$similar_idx]}")
  parsed_options_argcount+=("${options_argcount[$similar_idx]}")
  parsed_options_value+=("$value")
  parsed_types+=('o')
# return [o]
  }


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
      options_short+=("$short")
      options_long+=('')
      options_argcount+=(0)
      options_value+=(false)
#     if tokens.error is DocoptExit:
      parsed_options_short+=("$short")
      parsed_options_long+=('')
      parsed_options_argcount+=(0)
      parsed_options_value+=(true)
      parsed_types+=('o')
#       o = Option(short, None, 0, True)
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
    parsed_options_short+=("$short")
    parsed_options_long+=("${options_long[$similar_idx]}")
    parsed_options_argcount+=("${options_argcount[$similar_idx]}")
    parsed_options_value+=("$value")
    parsed_types+=('o')
#   parsed.append(o)
  done
# return parsed
}

parse_argv() {
# def parse_argv(tokens, options, options_first=False):
# """Parse command-line argument vector.

# If options_first:
#   argv ::= [ long | shorts ]* [ argument ]* [ '--' [ argument ]* ] ;
# else:
#   argv ::= [ long | shorts | argument ]* [ '--' [ argument ]* ] ;

# """
# parsed = []
  while [[ ${#argv[@]} -gt 0 ]]; do
# while tokens.current() is not None:
    if [[ ${argv[0]} == "--" ]]; then
#   if tokens.current() == '--':
      for arg in "${argv[@]}"; do
        parsed_arguments+=("$arg")
        parsed_types+=('a')
      done
      return
#     return parsed + [Argument(None, v) for v in tokens]
    elif [[ ${argv[0]} = --* ]]; then
#   elif tokens.current().startswith('--'):
      parse_long
#     parsed += parse_long(tokens, options)
    elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then
#   elif tokens.current().startswith('-') and tokens.current() != '-':
      parse_shorts
#     parsed += parse_shorts(tokens, options)
    elif $options_first; then
#   elif options_first:
      for arg in "${argv[@]}"; do
        parsed_arguments+=("$arg")
        parsed_types+=('a')
      done
      return
#     return parsed + [Argument(None, v) for v in tokens]
    else
#   else:
      parsed_arguments+=("$arg")
      parsed_types+=('a')
      argv=("${argv[@]:1}")
#     parsed.append(Argument(None, tokens.move()))
    fi
  done
# return parsed
}

# def docopt(doc, argv=None, help=True, version=None, options_first=False):
docopt() {
  local doc='
Naval Fate.

Usage:
  naval_fate.py ship new <name>...
  naval_fate.py ship <name> move <x> <y> [--speed=<kn>] [-f...]
  naval_fate.py ship shoot <x> <y>
  naval_fate.py up...
  naval_fate.py do ARGS...
  naval_fate.py mine (set|remove) <x> <y> [--moored|--drifting]
  naval_fate.py -h | --help
  naval_fate.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.
'
  # local help=true
  # local version=''
  options_first=false
  eval "$(./docopt.py <<<"$doc")"
  debug_var "options_short" "${options_short[@]}"
  debug_var "options_long" "${options_long[@]}"
  debug_var "options_argcount" "${options_argcount[@]}"
  debug_var "options_value" "${options_value[@]}"

  parsed_options_short=()
  parsed_options_long=()
  parsed_options_argcount=()
  parsed_options_value=()
  parsed_arguments=()
  parsed_types=()
  argv=("$@")
  parse_argv
  debug_var "parsed_options_short" "${parsed_options_short[@]}"
  debug_var "parsed_options_long" "${parsed_options_long[@]}"
  debug_var "parsed_options_argcount" "${parsed_options_argcount[@]}"
  debug_var "parsed_options_value" "${parsed_options_value[@]}"
}

debug_var() {
  local varname=$1
  shift
  printf "%s: " "$varname"
  if [[ $# -eq 1 ]]; then
    printf "%s" "$2"
  else
    printf "'%s' " "$@"
  fi
  printf "\n"
}

die() {
  # shellcheck disable=2059
  printf "$1\n" "$2" >&2
  exit 1
}

docopt "$@"
