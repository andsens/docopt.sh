#!/usr/bin/env bash


# Some comments

doc="Test program

Usage:
  test-program.sh [options] MESSAGE

Options:
  -h --help  This screen
"
# docopt parser below, refresh this parser with `docopt.sh test-program.sh`
docopt() {
  docopt_setup "$@"
  parse_argv
  docopt_extras
  local i=0
  while [[ $i -lt ${#parsed_params[@]} ]]; do left+=("$i"); ((i++)); done
  if ! root; then
    docopt_help
    exit 1
  fi
  type defaults &>/dev/null && defaults
  if [[ ${#left[@]} -gt 0 ]]; then
    docopt_help
    exit 1
  fi
  return 0
}
optional() {
  local pattern
  for pattern in "$@"; do
    $pattern
  done
  return 0
}
# $1=variable name
# $2=is it a list?
# $3=option idx to find in the options list (or 'a' for 'argument')
_value() {
  local i
  local needle=${3:-'a'}
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == "$needle" ]]; then
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      $test_match && return 0
      local value
      value=$(printf -- "%q" "${parsed_values[$l]}")
      if [[ $2 == true ]]; then
        eval "$1+=($value)"
      else
        eval "$1=$value"
      fi
      return 0
    fi
  done
  return 1
}
required() {
  local initial_left=("${left[@]}")
  local pattern
  local unset_test_match=true
  $test_match && unset_test_match=false
  test_match=true
  for pattern in "$@"; do
    if ! $pattern; then
      left=("${initial_left[@]}")
      $unset_test_match && test_match=false
      return 1
    fi
  done
  if $unset_test_match; then
    test_match=false
    left=("${initial_left[@]}")
    for pattern in "$@"; do $pattern; done
  fi
  return 0
}
docopt_extras() {
  local idx
  if $docopt_help; then
    for idx in "${parsed_params[@]}"; do
      [[ $idx == 'a' ]] && continue
      if [[ ${options_short[$idx]} == "-h" || ${options_long[$idx]} == "--help" ]]; then
        docopt_help
        exit 0
      fi
    done
  fi
  if [[ -n $docopt_version ]]; then
    for idx in "${parsed_params[@]}"; do
      [[ $idx == 'a' ]] && continue
      if [[ ${options_long[$idx]} == "--version" ]]; then
        printf "%s\n" "$docopt_version"
        exit 0
      fi
    done
  fi
}
parse_argv() {
  while [[ ${#argv[@]} -gt 0 ]]; do
    if [[ ${argv[0]} == "--" ]]; then
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      return
    elif [[ ${argv[0]} = --* ]]; then
      parse_long
    elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then
      parse_shorts
    elif $docopt_options_first; then
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      return
    else
      parsed_params+=('a')
      parsed_values+=("${argv[0]}")
      argv=("${argv[@]:1}")
    fi
  done
}
# $1=variable name
# $2=is it a list?
# $3=option idx to find in the options list
_switch() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == "$3" ]]; then
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      $test_match && return 0
      if [[ $2 == true ]]; then
        eval "(($1++))"
      else
        eval "$1=true"
      fi
      return 0
    fi
  done
  return 1
}
parse_long() {
  token=${argv[0]}
  long=${token%%=*}
  value=${token#*=}
  argv=("${argv[@]:1}")
  [[ $token == --* ]] || assert_fail
  if [[ $token = *=* ]]; then
    eq='='
  else
    eq=''
    value=false
  fi
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
  if [[ ${#similar[@]} -eq 0 ]]; then
    i=0
    for o in "${options_long[@]}"; do
      if [[ $o == $long* ]]; then
        similar+=("$long")
        [[ $similar_idx == false ]] && similar_idx=$i
      fi
      ((i++))
    done
  fi
  if [[ ${#similar[@]} -gt 1 ]]; then
    docopt_error "$(printf "%s is not a unique prefix: %s?" "$long" "${similar[*]}")"
  elif [[ ${#similar[@]} -lt 1 ]]; then
    if [[ $eq == '=' ]]; then
      argcount=1
    else
      argcount=0
    fi
    similar_idx=${#options_short[@]}
    if [[ argcount -eq 0 ]]; then
      value=true
    fi
    options_short+=('')
    options_long+=("$long")
    options_argcount+=("$argcount")
  else
    if [[ ${options_argcount[$similar_idx]} -eq 0 ]]; then
      if [[ $value != false ]]; then
        docopt_error "$(printf "%s must not have an argument" "${options_long[$similar_idx]}")"
      fi
    else
      if [[ $value == false ]]; then
        if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
          docopt_error "$(printf "%s requires argument" "$long")"
        fi
        value=${argv[0]}
        argv=("${argv[@]:1}")
      fi
    fi
    if [[ $value == false ]]; then
      value=true
    fi
  fi
  parsed_params+=("$similar_idx")
  parsed_values+=("$value")
}
parse_shorts() {
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
      docopt_error "$(printf "%s is specified ambiguously %d times" "$short" "${#similar[@]}")"
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
            docopt_error "$(printf "%s requires argument" "$short")"
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
}
req_1(){ required req_2;}
req_2(){ required optional_1 arg_1;}
optional_1(){ optional optional_2;}
optional_2(){ optional opt_1;}
opt_1(){ _switch ___help false 0;}
arg_1(){ _value _MESSAGE false;}
root(){ req_1;}
docopt_help() {
  printf -- "%s" "$doc"
}

docopt_error() {
  printf "%s\n" "$1"
  exit 1
}
docopt_setup() {
  argv=("$@")
  options_short=(-h)
  options_long=(--help)
  options_argcount=(0)
  param_names=(___help _MESSAGE)
  parsed_params=()
  parsed_values=()
  left=()
  test_match=false
  docopt_options_first=${docopt_options_first:-false}
  docopt_help=${docopt_help:-true}
  docopt_version=${docopt_version:-}
  for var in "${param_names[@]}"; do
    if declare -p "$var" &>/dev/null; then
      printf "Variable naming collision: %s\nUse a different prefix or rename your arguments." "$var"
      exit 1
    fi
  done
}
docopt_defaults() {
  ___help=${___help:-false}
  _MESSAGE=${_MESSAGE:-}
}
docopt_check() {
  local current_doc_hash
  current_doc_hash=$(printf "%s" "$doc" | shasum -a 256 | cut -f 1 -d " ")
  if [[ $current_doc_hash != "26ba0965debc9ac68dba03aeef1a302448493ea104c1af0af9bf4645cd3d41bd" ]]; then
    printf "The current usage doc (%s) does not match what the parser was generated with (26ba0965debc9ac68dba03aeef1a302448493ea104c1af0af9bf4645cd3d41bd)\n" "$current_doc_hash" >&2
    exit 1;
  fi
}
docopt_check
# docopt parser above, refresh this parser with `docopt.sh test-program.sh`

docopt "$@"

echo "$_MESSAGE"

# Some more comments
