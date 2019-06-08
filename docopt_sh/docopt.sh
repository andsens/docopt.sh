#!/usr/bin/env bash

docopt() {
  "LIBRARY SOURCE"
  docopt_usage="DOC VALUE"
  docopt_digest="DOC DIGEST"
  docopt_short_usage="${docopt_usage:"SHORT USAGE START":"SHORT USAGE LENGTH"}"
  docopt_shorts=("SHORTS")
  docopt_longs=("LONGS")
  docopt_argcount=("ARGCOUNT")
  docopt_param_names=("PARAM NAMES")
  "NODES"
  docopt_parse "$@"
  "DEFAULTS"
  ${docopt_teardown:-true} && docopt_do_teardown "MAX NODE IDX"
}

docopt_do_teardown() {
  local max_node_idx=$1
  local var
  for var in "${docopt_param_names[@]}"; do
    unset "docopt_var_$var"
  done
  local i
  for ((i=0; i<=max_node_idx; i++)); do
    unset -f "docopt_node_$i"
  done
  unset docopt_usage docopt_digest docopt_short_usage docopt_shorts \
  docopt_longs docopt_argcount docopt_param_names docopt_argv docopt_left \
  docopt_parsed_params docopt_parsed_values docopt_testmatch
  unset -f docopt docopt_parse \
  docopt_either docopt_oneormore docopt_optional docopt_required \
  docopt_command docopt_switch docopt_value docopt_error \
  docopt_parse_long docopt_parse_shorts docopt_node_root docopt_do_teardown
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
  [[ -n $1 ]] && printf "%s\n" "$1"
  printf "%s\n" "${docopt_short_usage}"
  exit 1
}

docopt_parse() {
  if ${docopt_doc_check:-true}; then
    local doc_hash
    doc_hash=$(printf "%s" "$docopt_usage" | shasum -a 256)
    if [[ ${doc_hash:0:5} != "$docopt_digest" ]]; then
      printf "The current usage doc (%s) does not match what the parser was generated with (%s)\n" \
        "${doc_hash:0:5}" "$docopt_digest" >&2
      exit 70
    fi
  fi

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
    elif ${docopt_options_first:-false}; then
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
  if ${docopt_add_help:-true}; then
    for idx in "${docopt_parsed_params[@]}"; do
      [[ $idx = 'a' ]] && continue
      if [[ ${docopt_shorts[$idx]} = "-h" || ${docopt_longs[$idx]} = "--help" ]]; then
        printf -- "%s\n" "$docopt_usage"
        exit 0
      fi
    done
  fi
  if [[ ${docopt_program_version:-false} != 'false' ]]; then
    for idx in "${docopt_parsed_params[@]}"; do
      [[ $idx = 'a' ]] && continue
      if [[ ${docopt_longs[$idx]} = "--version" ]]; then
        printf "%s\n" "$docopt_program_version"
        exit 0
      fi
    done
  fi

  local i=0
  while [[ $i -lt ${#docopt_parsed_params[@]} ]]; do
    docopt_left+=("$i")
    ((i++))
  done

  if ! docopt_required root || [ ${#docopt_left[@]} -gt 0 ]; then
    docopt_error
  fi
  return 0
}
