#!/usr/bin/env bash

docopt() {
  "LIBRARY"
  set -e
  # substring of doc where leading & trailing newlines have been trimmed
  trimmed_doc="DOC VALUE"
  # substring of doc containing the Usage: part (i.e. no Options: or other notes)
  usage="DOC USAGE"
  # shortened shasum of doc from which the parser was generated
  digest="DOC DIGEST"
  # 3 lists representing option metadata
  # names for short options
  shorts=("SHORTS")
  # names for long options
  longs=("LONGS")
  # argument counts for options, 0 or 1
  argcounts=("ARGCOUNTS")

  # Nodes. This is the AST representing the parsed doc.
  "NODES"

  # shellcheck disable=2016
  cat <<<' docopt_exit() {
  [[ -n $1 ]] && printf "%s\n" "$1" >&2
  printf "%s\n" ""DOC USAGE"" >&2
  exit 1
}'
  # unset the "var_" prefixed variables that will be used for internal assignment
  unset "INTERNAL VARNAMES"
  # invoke main parsing function
  parse "ROOT NODE IDX" "$@"
  # if there are no variables to be set docopt() will exit here
  # shellcheck disable=2157,2140
  "EARLY RETURN"
  # shellcheck disable=2034
  local prefix=${DOCOPT_PREFIX:-''}

  # Unset exported variables from parent shell
  # that may clash with names derived from the doc
  unset "OUTPUT VARNAMES"
  # Assign internal varnames to output varnames and set defaults
  "OUTPUT VARNAMES ASSIGNMENTS"

  # Workaround for bash-4.3 bug
  # The following script will not work in bash 4.3.0 (and only that version)
  # #!tests/bash-versions/bash-4.3/bash
  # fn() {
  #   decl=$(X=(A B); declare -p X)
  #   eval "$decl"
  #   declare -p X
  # }
  # fn
  # Adding "declare X" before "eval" fixes the issue, but we don't know the
  # variable names, so instead we just output the `declare`s twice
  # in bash-4.3.
  local docopt_i=1
  [[ $BASH_VERSION =~ ^4.3 ]] && docopt_i=2
  for ((;docopt_i>0;docopt_i--)); do
  declare -p "OUTPUT VARNAMES"
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

parse() {
  if ${DOCOPT_DOC_CHECK:-true}; then
    local doc_hash
    if doc_hash=$(printf "%s" "$DOC" | (sha256sum 2>/dev/null || shasum -a 256)); then
      # shellcheck disable=SC2154
      if [[ ${doc_hash:0:5} != "$digest" ]]; then
        stderr "The current usage doc (${doc_hash:0:5}) does not match \
what the parser was generated with (${digest})
Run \`docopt.sh\` to refresh the parser."
        _return 70
      fi
    fi
  fi

  local root_idx=$1
  shift
  argv=("$@")
  # Typed parsed parameter indices and values array in the order they
  # appear in argv.
  # Example:
  # Usage: prog -s --val=OPTARG command ARG
  # $ prog command --val=optval "arg val" -s
  # -> (a:command 1:optval a:"arg val" 1:true)
  parsed=()
  # Array containing indices of the remaining unparsed params.
  # Initially filled with 0 through ${#parsed[@]}
  # parsers will remove indices on successful parsing
  left=()
  # testing depth counter, when >0 nodes only check for potential matches
  # when ==0 leafs will set the actual variable when a match is found
  testdepth=0

  # loop through the parameters and parse them one param at a time
  local arg
  while [[ ${#argv[@]} -gt 0 ]]; do
    if [[ ${argv[0]} = "--" ]]; then
      # No more options allowed.
      # Parse everything from here on out as commands or arguments. Then break.
      for arg in "${argv[@]}"; do
        parsed+=("a:$arg")
      done
      break
    elif [[ ${argv[0]} = --* ]]; then
      parse_long
    elif [[ ${argv[0]} = -* && ${argv[0]} != "-" ]]; then
      parse_shorts
    elif ${DOCOPT_OPTIONS_FIRST:-false}; then
      # First non-option encountered and all options must be specified first.
      # Parse everything from here on out as commands or arguments. Then break.
      for arg in "${argv[@]}"; do
        parsed+=("a:$arg")
      done
      break
    else
      parsed+=("a:${argv[0]}")
      argv=("${argv[@]:1}")
    fi
  done

  local param
  if ${DOCOPT_ADD_HELP:-true} || [[ ${DOCOPT_PROGRAM_VERSION:-false} != 'false' ]]; then
    # Early exit if -h is specified
    for param in "${parsed[@]}"; do
      local idx=${param%%:*}
      [[ $idx = 'a' ]] && continue
      if ${DOCOPT_ADD_HELP:-true} && [[ ${shorts[$idx]} = "-h" || ${longs[$idx]} = "--help" ]]; then
        # shellcheck disable=SC2154
        stdout "$trimmed_doc"
        _return 0
      fi
      if [[ ${DOCOPT_PROGRAM_VERSION:-false} != 'false' && ${longs[$idx]} = "--version" ]]; then
        stdout "$DOCOPT_PROGRAM_VERSION"
        _return 0
      fi
    done
  fi

  # Populate the array of remaining indices to parse
  local i=0
  while [[ $i -lt ${#parsed[@]} ]]; do
    left+=("$i")
    ((i++)) || true
  done

  # Run through the parsing tree, fail if not all params could be parsed.
  if ! "node_$root_idx" || [ ${#left[@]} -gt 0 ]; then
    error
  fi
  return 0
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
    parsed+=("$match:$value")
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
  parsed+=("$match:$value")
}

sequence() {
  local initial_left=("${left[@]}")
  local node_idx
  # Increase testdepth, so we don't partially set variables and then fail
  ((testdepth++)) || true
  # Check if we can match the entire subtree
  for node_idx in "$@"; do
    if ! "node_$node_idx"; then
      # Unable to match the entire subtree, reset the remaining params
      left=("${initial_left[@]}")
      ((testdepth--)) || true
      return 1
    fi
  done
  # Decrease testdepth and let subtree set the variables
  if [[ $((--testdepth)) -eq 0 ]]; then
    left=("${initial_left[@]}")
    for node_idx in "$@"; do
      "node_$node_idx"
    done
  fi
  return 0
}

choice() {
  local initial_left=("${left[@]}")
  local best_match_idx
  local match_count
  local node_idx
  # Increase testdepth, so that we can test all subtrees without setting variables
  ((testdepth++)) || true
  # Determine the best subtree match
  for node_idx in "$@"; do
    if "node_$node_idx"; then
      # Subtree matches
      # Make it the best match if the previous best match consumed fewer params
      if [[ -z $match_count || ${#left[@]} -lt $match_count ]]; then
        best_match_idx=$node_idx
        match_count=${#left[@]}
      fi
    fi
    left=("${initial_left[@]}")
  done
  # Check if any subtree matched
  if [[ -n $best_match_idx ]]; then
    # Decrease testdepth and let the best-matching subtree set the variables
    if [[ $((--testdepth)) -eq 0 ]]; then
      "node_$best_match_idx"
    fi
    return 0
  fi
  # No subtree matched, reset the remaining params
  left=("${initial_left[@]}")
  return 1
}

optional() {
  local node_idx
  # Parse subtree, stop parsing when we can't match any longer
  for node_idx in "$@"; do
    "node_$node_idx"
  done
  # Always succeed
  return 0
}

repeatable() {
  local matched=false
  local prev=${#left[@]}
  # Parse until we can't any longer
  while "node_$1"; do
    matched=true
    # Nothing was removed from the remaining params, so stop looping
    # This happens when an optional param can be repeated.
    # An optional subtree parser never fails.
    [[ $prev -eq ${#left[@]} ]] && break
    prev=${#left[@]}
  done
  if $matched; then
    return 0
  fi
  return 1
}

switch() {
  # Run though remaining params and check if there is an argument-less option,
  # a command, or argument separator in there
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed[$l]} = "$2" || ${parsed[$l]} = "$2":* ]]; then
      # Name of the option/command matches, remove the param from remaining params
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      [[ $testdepth -gt 0 ]] && return 0
      # Set the variable if we are not in testing mode
      if [[ $3 = true ]]; then
        # Switch is repeatable, increase a counter
        eval "((var_$1++))" || true
      else
        # Switch is not repeatable, set to true
        eval "var_$1=true"
      fi
      return 0
    elif [[ ${parsed[$l]} = a:* && $2 = a:* ]]; then
      # Fail if we were to parse a non-option and we encountered a non-option
      # where the name doesn't match
      return 1
    fi
  done
  # No switches left, fail
  return 1
}

value() {
  # Run though remaining params and check if there is an argument or an option
  # with an argument in there
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed[$l]} = "$2":* ]]; then
      # Argument or option matches, remove the param from remaining params
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      [[ $testdepth -gt 0 ]] && return 0
      # Set the variable if we are not in testing mode
      local value
      value=$(printf -- "%q" "${parsed[$l]#*:}")
      if [[ $3 = true ]]; then
        # Value is repeatable, add it to the array
        eval "var_$1+=($value)"
      else
        # Value is not repeatable, set the value
        eval "var_$1=$value"
      fi
      return 0
    fi
  done
  return 1
}

stdout() {
  # docopt is eval'd. So any output to stdout will just be evaluated.
  # Output the message as a command that outputs the message instead.
  printf -- "cat <<'EOM'\n%s\nEOM\n" "$1"
}

stderr() {
  # stderr is not captured when doing `eval "$(docopt "$@")"', but
  # we do the same as in stdout for consistencies sake.
  printf -- "cat <<'EOM' >&2\n%s\nEOM\n" "$1"
}

error() {
  [[ -n $1 ]] && stderr "$1"
  # shellcheck disable=SC2154
  stderr "$usage"
  _return 1
}

_return() {
  # Same as in stdout(). An exit will not exit the parent program.
  # Output the command that does it to `eval' instead.
  printf -- "exit %d\n" "$1"
  exit "$1"
}

