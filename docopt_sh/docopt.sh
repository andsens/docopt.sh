#!/usr/bin/env bash

docopt() {
  docopt_run() {
    "LIBRARY SOURCE"
    docopt_doc="DOC VALUE"
    docopt_usage="DOC USAGE"
    docopt_digest="DOC DIGEST"
    docopt_shorts=("SHORTS")
    docopt_longs=("LONGS")
    docopt_argcount=("ARGCOUNT")
    "NODES"
    docopt_parse "ROOT NODE IDX" "$@" || exit $?
    # shellcheck disable=2016
    cat <<<' docopt_exit() {
  [[ -n $1 ]] && printf "%s\n" "$1" >&2
  printf "%s\n" ""DOC USAGE"" >&2
  exit 1
}'
    "OUTPUT TEARDOWN"
    # shellcheck disable=2157,2140
    "HAS VARS" || return 0
    # shellcheck disable=2034
    local docopt_prefix=${DOCOPT_PREFIX:-''}
    # Workaround for bash-4.3 bug
    # The following script will not work in bash 4.3.0 (and only that version)
    # #!tests/bash-versions/bash-4.3/bash
    # fn() {
    #   decl=$(X=(A B); declare -p X)
    #   eval "$decl"
    #   declare -p X
    # }
    # fn
    local docopt_loops=1
    [[ $BASH_VERSION =~ ^4.3 ]] && docopt_loops=2
    # Adding "declare X" before "eval" fixes the issue, but we don't know the
    # variable names, so instead we just output the `declare`s twice
    # in bash-4.3.

    # Unset exported variables from parent shell
    unset "VAR NAMES"
    "DEFAULTS"
    local docopt_i=0
    for ((docopt_i=0;docopt_i<docopt_loops;docopt_i++)); do
    declare -p "VAR NAMES"
    done
  }
  local out
  if out=$(docopt_run "$@" 2>&1); then
    printf -- "%s\n" "$out"
  else
    local ret=$?
    if [ $ret -eq 85 ]; then
      printf -- "cat <<'EOM'\n%s\nEOM\nexit 0\n" "$out"
    else
      printf -- "cat <<'EOM' >&2\n%s\nEOM\nexit %d\n" "$out" "$ret"
    fi
  fi
}

lib_version_check() {
if [[ $1 != '"LIBRARY VERSION"' && ${DOCOPT_LIB_CHECK:-true} != 'false' ]]; then
  printf "The version of the included docopt library (%s) \
does not match the version of the invoking docopt parser (%s)\n" \
    '"LIBRARY VERSION"' "$1" >&2
  exit 70
fi
}

docopt_either() {
  local initial_left=("${docopt_left[@]}")
  local best_match_idx
  local match_count
  local node_idx
  local unset_testmatch=true
  $docopt_testmatch && unset_testmatch=false
  docopt_testmatch=true
  for node_idx in "$@"; do
    if "docopt_node_$node_idx"; then
      if [[ -z $match_count || ${#docopt_left[@]} -lt $match_count ]]; then
        best_match_idx=$node_idx
        match_count=${#docopt_left[@]}
      fi
    fi
    docopt_left=("${initial_left[@]}")
  done
  $unset_testmatch && docopt_testmatch=false
  if [[ -n $best_match_idx ]]; then
    "docopt_node_$best_match_idx"
    return 0
  fi
  docopt_left=("${initial_left[@]}")
  return 1
}

docopt_oneormore() {
  local i=0
  local prev=${#docopt_left[@]}
  while "docopt_node_$1"; do
    ((i++))
    [[ $prev -eq ${#docopt_left[@]} ]] && break
    prev=${#docopt_left[@]}
  done
  if [[ $i -ge 1 ]]; then
    return 0
  fi
  return 1
}

docopt_optional() {
  local node_idx
  for node_idx in "$@"; do
    "docopt_node_$node_idx"
  done
  return 0
}

docopt_required() {
  local initial_left=("${docopt_left[@]}")
  local node_idx
  local unset_testmatch=true
  $docopt_testmatch && unset_testmatch=false
  docopt_testmatch=true
  for node_idx in "$@"; do
    if ! "docopt_node_$node_idx"; then
      docopt_left=("${initial_left[@]}")
      $unset_testmatch && docopt_testmatch=false
      return 1
    fi
  done
  if $unset_testmatch; then
    docopt_testmatch=false
    docopt_left=("${initial_left[@]}")
    for node_idx in "$@"; do
      "docopt_node_$node_idx"
    done
  fi
  return 0
}

docopt_switch() {
  local i
  for i in "${!docopt_left[@]}"; do
    local l=${docopt_left[$i]}
    if [[ ${docopt_parsed_params[$l]} = "$2" ]]; then
      docopt_left=("${docopt_left[@]:0:$i}" "${docopt_left[@]:((i+1))}")
      $docopt_testmatch && return 0
      if [[ $3 = true ]]; then
        eval "((docopt_var_$1++))"
      else
        eval "docopt_var_$1=true"
      fi
      return 0
    fi
  done
  return 1
}

docopt_value() {
  local i
  for i in "${!docopt_left[@]}"; do
    local l=${docopt_left[$i]}
    if [[ ${docopt_parsed_params[$l]} = "$2" ]]; then
      docopt_left=("${docopt_left[@]:0:$i}" "${docopt_left[@]:((i+1))}")
      $docopt_testmatch && return 0
      local value
      value=$(printf -- "%q" "${docopt_parsed_values[$l]}")
      if [[ $3 = true ]]; then
        eval "docopt_var_$1+=($value)"
      else
        eval "docopt_var_$1=$value"
      fi
      return 0
    fi
  done
  return 1
}

docopt_command() {
  local i
  local name=${2:-$1}
  for i in "${!docopt_left[@]}"; do
    local l=${docopt_left[$i]}
    if [[ ${docopt_parsed_params[$l]} = 'a' ]]; then
      if [[ ${docopt_parsed_values[$l]} != "$name" ]]; then
        return 1
      fi
      docopt_left=("${docopt_left[@]:0:$i}" "${docopt_left[@]:((i+1))}")
      $docopt_testmatch && return 0
      if [[ $3 = true ]]; then
        eval "((docopt_var_$1++))"
      else
        eval "docopt_var_$1=true"
      fi
      return 0
    fi
  done
  return 1
}

docopt_parse_shorts() {
  local token=${docopt_argv[0]}
  local value
  docopt_argv=("${docopt_argv[@]:1}")
  [[ $token = -* && $token != --* ]] || assert_fail
  local remaining=${token#-}
  while [[ -n $remaining ]]; do
    local short="-${remaining:0:1}"
    remaining="${remaining:1}"
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
      docopt_error "$(printf "%s is specified ambiguously %d times" \
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
        if [[ $remaining = '' ]]; then
          if [[ ${#docopt_argv[@]} -eq 0 || ${docopt_argv[0]} = '--' ]]; then
            docopt_error "$(printf "%s requires argument" "$short")"
          fi
          value=${docopt_argv[0]}
          docopt_argv=("${docopt_argv[@]:1}")
        else
          value=$remaining
          remaining=''
        fi
      fi
      if [[ $value = false ]]; then
        value=true
      fi
    fi
    docopt_parsed_params+=("$match")
    docopt_parsed_values+=("$value")
  done
}

docopt_parse_long() {
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
    docopt_error "$(printf "%s is not a unique prefix: %s?" \
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
        docopt_error "$(printf "%s must not have an argument" \
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
}

docopt_error() {
  [[ -n $1 ]] && printf "%s\n" "$1" >&2
  printf "%s\n" "${docopt_usage}" >&2
  exit 1
}

docopt_do_teardown() {
  unset -f docopt_run docopt_parse docopt_either docopt_oneormore \
  docopt_optional docopt_required docopt_command docopt_switch docopt_value \
  docopt_parse_long docopt_parse_shorts docopt_error docopt_do_teardown
}

docopt_parse() {
  if ${DOCOPT_DOC_CHECK:-true}; then
    local doc_hash
    doc_hash=$(printf "%s" "$DOC" | shasum -a 256)
    if [[ ${doc_hash:0:5} != "$docopt_digest" ]]; then
      printf "The current usage doc (%s) does not match what the parser was \
generated with (%s)\nRun \`docopt.sh\` to refresh the parser.\n" \
        "${doc_hash:0:5}" "$docopt_digest"
      exit 70
    fi
  fi

  local root_idx=$1
  shift
  docopt_argv=("$@")
  docopt_parsed_params=()
  docopt_parsed_values=()
  docopt_left=()
  docopt_testmatch=false

  local arg
  while [[ ${#docopt_argv[@]} -gt 0 ]]; do
    if [[ ${docopt_argv[0]} = "--" ]]; then
      for arg in "${docopt_argv[@]}"; do
        docopt_parsed_params+=('a')
        docopt_parsed_values+=("$arg")
      done
      break
    elif [[ ${docopt_argv[0]} = --* ]]; then
      docopt_parse_long
    elif [[ ${docopt_argv[0]} = -* && ${docopt_argv[0]} != "-" ]]; then
      docopt_parse_shorts
    elif ${DOCOPT_OPTIONS_FIRST:-false}; then
      for arg in "${docopt_argv[@]}"; do
        docopt_parsed_params+=('a')
        docopt_parsed_values+=("$arg")
      done
      break
    else
      docopt_parsed_params+=('a')
      docopt_parsed_values+=("${docopt_argv[0]}")
      docopt_argv=("${docopt_argv[@]:1}")
    fi
  done
  local idx
  if ${DOCOPT_ADD_HELP:-true}; then
    for idx in "${docopt_parsed_params[@]}"; do
      [[ $idx = 'a' ]] && continue
      if [[ ${docopt_shorts[$idx]} = "-h" || ${docopt_longs[$idx]} = "--help" ]]; then
        printf -- "%s\n" "$docopt_doc"
        exit 85
      fi
    done
  fi
  if [[ ${DOCOPT_PROGRAM_VERSION:-false} != 'false' ]]; then
    for idx in "${docopt_parsed_params[@]}"; do
      [[ $idx = 'a' ]] && continue
      if [[ ${docopt_longs[$idx]} = "--version" ]]; then
        printf "%s\n" "$DOCOPT_PROGRAM_VERSION"
        exit 85
      fi
    done
  fi

  local i=0
  while [[ $i -lt ${#docopt_parsed_params[@]} ]]; do
    docopt_left+=("$i")
    ((i++))
  done

  if ! docopt_required "$root_idx" || [ ${#docopt_left[@]} -gt 0 ]; then
    docopt_error
  fi
  return 0
}
