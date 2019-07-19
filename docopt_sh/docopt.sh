#!/usr/bin/env bash

docopt() {
  "LIBRARY"
  set -e
  doc="DOC VALUE"
  usage="DOC USAGE"
  digest="DOC DIGEST"
  shorts=("SHORTS")
  longs=("LONGS")
  argcounts=("ARGCOUNT")
  "NODES"
  # shellcheck disable=2016
  cat <<<' docopt_exit() {
  [[ -n $1 ]] && printf "%s\n" "$1" >&2
  printf "%s\n" ""DOC USAGE"" >&2
  exit 1
}'
  parse "ROOT NODE IDX" "$@"
  # shellcheck disable=2157,2140
  "HAS VARS" || return 0
  # shellcheck disable=2034
  local prefix=${DOCOPT_PREFIX:-''}
  # Workaround for bash-4.3 bug
  # The following script will not work in bash 4.3.0 (and only that version)
  # #!tests/bash-versions/bash-4.3/bash
  # fn() {
  #   decl=$(X=(A B); declare -p X)
  #   eval "$decl"
  #   declare -p X
  # }
  # fn
  local declares=1
  [[ $BASH_VERSION =~ ^4.3 ]] && declares=2
  # Adding "declare X" before "eval" fixes the issue, but we don't know the
  # variable names, so instead we just output the `declare`s twice
  # in bash-4.3.

  # Unset exported variables from parent shell
  unset "VAR NAMES"
  "DEFAULTS"
  local i=0
  for ((i=0;i<declares;i++)); do
  declare -p "VAR NAMES"
  done
}

lib_version_check() {
if [[ $1 != '"LIBRARY VERSION"' && ${DOCOPT_LIB_CHECK:-true} != 'false' ]]; then
  printf -- "cat <<'EOM' >&2\nThe version of the included docopt library (%s) \
does not match the version of the invoking docopt parser (%s)\nEOM\nexit 70\n" \
    '"LIBRARY VERSION"' "$1"
  exit 70
fi
}

either() {
  local initial_left=("${left[@]}")
  local best_match_idx
  local match_count
  local node_idx
  local unset_testmatch=true
  $testmatch && unset_testmatch=false
  testmatch=true
  for node_idx in "$@"; do
    if "node_$node_idx"; then
      if [[ -z $match_count || ${#left[@]} -lt $match_count ]]; then
        best_match_idx=$node_idx
        match_count=${#left[@]}
      fi
    fi
    left=("${initial_left[@]}")
  done
  $unset_testmatch && testmatch=false
  if [[ -n $best_match_idx ]]; then
    "node_$best_match_idx"
    return 0
  fi
  left=("${initial_left[@]}")
  return 1
}

oneormore() {
  local i=0
  local prev=${#left[@]}
  while "node_$1"; do
    ((i++)) || true
    [[ $prev -eq ${#left[@]} ]] && break
    prev=${#left[@]}
  done
  if [[ $i -ge 1 ]]; then
    return 0
  fi
  return 1
}

optional() {
  local node_idx
  for node_idx in "$@"; do
    "node_$node_idx"
  done
  return 0
}

required() {
  local initial_left=("${left[@]}")
  local node_idx
  local unset_testmatch=true
  $testmatch && unset_testmatch=false
  testmatch=true
  for node_idx in "$@"; do
    if ! "node_$node_idx"; then
      left=("${initial_left[@]}")
      $unset_testmatch && testmatch=false
      return 1
    fi
  done
  if $unset_testmatch; then
    testmatch=false
    left=("${initial_left[@]}")
    for node_idx in "$@"; do
      "node_$node_idx"
    done
  fi
  return 0
}

switch() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} = "$2" ]]; then
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      $testmatch && return 0
      if [[ $3 = true ]]; then
        eval "((var_$1++))" || true
      else
        eval "var_$1=true"
      fi
      return 0
    fi
  done
  return 1
}

value() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} = "$2" ]]; then
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      $testmatch && return 0
      local value
      value=$(printf -- "%q" "${parsed_values[$l]}")
      if [[ $3 = true ]]; then
        eval "var_$1+=($value)"
      else
        eval "var_$1=$value"
      fi
      return 0
    fi
  done
  return 1
}

_command() {
  local i
  local name=${2:-$1}
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} = 'a' ]]; then
      if [[ ${parsed_values[$l]} != "$name" ]]; then
        return 1
      fi
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      $testmatch && return 0
      if [[ $3 = true ]]; then
        eval "((var_$1++)) || true"
      else
        eval "var_$1=true"
      fi
      return 0
    fi
  done
  return 1
}

parse_shorts() {
  local token=${argv[0]}
  local value
  argv=("${argv[@]:1}")
  [[ $token = -* && $token != --* ]] || _return 88
  local remaining=${token#-}
  while [[ -n $remaining ]]; do
    local short="-${remaining:0:1}"
    remaining="${remaining:1}"
    local i=0
    local similar=()
    local match=false
    for o in "${shorts[@]}"; do
      if [[ $o = "$short" ]]; then
        similar+=("$short")
        [[ $match = false ]] && match=$i
      fi
      ((i++)) || true
    done
    if [[ ${#similar[@]} -gt 1 ]]; then
      error "${short} is specified ambiguously ${#similar[@]} times"
    elif [[ ${#similar[@]} -lt 1 ]]; then
      match=${#shorts[@]}
      value=true
      shorts+=("$short")
      longs+=('')
      argcounts+=(0)
    else
      value=false
      if [[ ${argcounts[$match]} -ne 0 ]]; then
        if [[ $remaining = '' ]]; then
          if [[ ${#argv[@]} -eq 0 || ${argv[0]} = '--' ]]; then
            error "${short} requires argument"
          fi
          value=${argv[0]}
          argv=("${argv[@]:1}")
        else
          value=$remaining
          remaining=''
        fi
      fi
      if [[ $value = false ]]; then
        value=true
      fi
    fi
    parsed_params+=("$match")
    parsed_values+=("$value")
  done
}

parse_long() {
  local token=${argv[0]}
  local long=${token%%=*}
  local value=${token#*=}
  local argcount
  argv=("${argv[@]:1}")
  [[ $token = --* ]] || _return 88
  if [[ $token = *=* ]]; then
    eq='='
  else
    eq=''
    value=false
  fi
  local i=0
  local similar=()
  local match=false
  for o in "${longs[@]}"; do
    if [[ $o = "$long" ]]; then
      similar+=("$long")
      [[ $match = false ]] && match=$i
    fi
    ((i++)) || true
  done
  if [[ $match = false ]]; then
    i=0
    for o in "${longs[@]}"; do
      if [[ $o = $long* ]]; then
        similar+=("$long")
        [[ $match = false ]] && match=$i
      fi
      ((i++)) || true
    done
  fi
  if [[ ${#similar[@]} -gt 1 ]]; then
    error "${long} is not a unique prefix: ${similar[*]}?"
  elif [[ ${#similar[@]} -lt 1 ]]; then
    [[ $eq = '=' ]] && argcount=1 || argcount=0
    match=${#shorts[@]}
    [[ $argcount -eq 0 ]] && value=true
    shorts+=('')
    longs+=("$long")
    argcounts+=("$argcount")
  else
    if [[ ${argcounts[$match]} -eq 0 ]]; then
      if [[ $value != false ]]; then
        error "${longs[$match]} must not have an argument"
      fi
    elif [[ $value = false ]]; then
      if [[ ${#argv[@]} -eq 0 || ${argv[0]} = '--' ]]; then
        error "${long} requires argument"
      fi
      value=${argv[0]}
      argv=("${argv[@]:1}")
    fi
    if [[ $value = false ]]; then
      value=true
    fi
  fi
  parsed_params+=("$match")
  parsed_values+=("$value")
}

stdout() {
  printf -- "cat <<'EOM'\n%s\nEOM\n" "$1"
}

stderr() {
  printf -- "cat <<'EOM' >&2\n%s\nEOM\n" "$1"
}

error() {
  [[ -n $1 ]] && stderr "$1"
  stderr "$usage"
  _return 1
}

_return() {
  printf -- "exit %d\n" "$1"
  exit "$1"
}

parse() {
  if ${DOCOPT_DOC_CHECK:-true}; then
    local doc_hash
    doc_hash=$(printf "%s" "$DOC" | shasum -a 256)
    if [[ ${doc_hash:0:5} != "$digest" ]]; then
      stderr "The current usage doc (${doc_hash:0:5}) does not match \
what the parser was generated with (${digest})
Run \`docopt.sh\` to refresh the parser."
      _return 70
    fi
  fi

  local root_idx=$1
  shift
  argv=("$@")
  parsed_params=()
  parsed_values=()
  left=()
  testmatch=false

  local arg
  while [[ ${#argv[@]} -gt 0 ]]; do
    if [[ ${argv[0]} = "--" ]]; then
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      break
    elif [[ ${argv[0]} = --* ]]; then
      parse_long
    elif [[ ${argv[0]} = -* && ${argv[0]} != "-" ]]; then
      parse_shorts
    elif ${DOCOPT_OPTIONS_FIRST:-false}; then
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      break
    else
      parsed_params+=('a')
      parsed_values+=("${argv[0]}")
      argv=("${argv[@]:1}")
    fi
  done
  local idx
  if ${DOCOPT_ADD_HELP:-true}; then
    for idx in "${parsed_params[@]}"; do
      [[ $idx = 'a' ]] && continue
      if [[ ${shorts[$idx]} = "-h" || ${longs[$idx]} = "--help" ]]; then
        stdout "$doc"
        _return 0
      fi
    done
  fi
  if [[ ${DOCOPT_PROGRAM_VERSION:-false} != 'false' ]]; then
    for idx in "${parsed_params[@]}"; do
      [[ $idx = 'a' ]] && continue
      if [[ ${longs[$idx]} = "--version" ]]; then
        stdout "$DOCOPT_PROGRAM_VERSION"
        _return 0
      fi
    done
  fi

  local i=0
  while [[ $i -lt ${#parsed_params[@]} ]]; do
    left+=("$i")
    ((i++)) || true
  done

  if ! required "$root_idx" || [ ${#left[@]} -gt 0 ]; then
    error
  fi
  return 0
}
