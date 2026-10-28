#!/usr/bin/env bash

docopt() {
  # This function will always be directly inlined in the script.
  # It contains all the specifics of $DOC, while the remaining functions
  # are generic. All strings with uppercase letters a placeholders.
  # The code relies heavily on global variables. Since docopt is called
  # in a subshell, this shouldn't be a problem for the caller. It does
  # however mean that we must initialize all global variables before use to
  # avoid weird behavior caused by naming clashes.

  # The library, can be either the complete inline definition of all functions
  # or a `source` call
  "LIBRARY"
  # return on errors, I can't remember why this is placed after the library
  # I just remember that it's important for some reason when sourcing :-)
  set -e
  # substring of doc where leading & trailing newlines have been trimmed
  trimmed_doc="DOC VALUE"
  # substring of doc containing the Usage: part (i.e. no Options: or other notes)
  usage="DOC USAGE"
  # shortened shasum of doc from which the parser was generated
  digest="DOC DIGEST"
  # Options array. Each entry consists of:
  # * short name
  # * long name
  # * argcount (0 or 1)
  # The items are space separated. The order matches the AST node numbering
  options=("OPTIONS")
  # This is the AST representing the parsed doc. The last node is the root.
  # Options are first, as mentioned above. The comments above each node is
  # shows what part of the DOC it is parsing (with line numbers).

  "NODES"

  # Exit function that is callable from the parent shell. It outputs an
  # optional error message and then prints the usage part of the doc
  # shellcheck disable=2016
  cat <<<' docopt_exit() {
  [[ -n $1 ]] && printf "%s\n" "$1" >&2
  printf "%s\n" ""DOC USAGE"" >&2
  exit 1
}'

  local varnames=("VARNAMES") varname
  # unset the "var_" prefixed variables that will be used for internal assignment
  for varname in "${varnames[@]}"; do
    unset "var_$varname"
  done
  # invoke main parsing function
  parse "ROOT NODE IDX" "$@"
  # if there are no variables to be set docopt() will exit here
  # shellcheck disable=2157,2140
  "EARLY RETURN"
  # The variable name prefix. Either $DOCOPT_PREFIX or the value of --prefix
  # shellcheck disable=2034
  local p="PREFIX"

  # Unset exported variables from parent shell
  # that may clash with names derived from the doc
  for varname in "${varnames[@]}"; do
    unset "$p$varname"
  done
  # Assign internal varnames to output varnames and set defaults
  "OUTPUT VARNAMES ASSIGNMENTS"
  # Never runs. shellcheck can't see the assignments in the eval above, so
  # without this it complains about the variables not being assigned (SC2154)
  # wherever they are used in the script.
  "SHELLCHECK ASSIGNMENTS"

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
    for varname in "${varnames[@]}"; do
      declare -p "$p$varname"
    done
  done
}

lib_version_check() {
  # Version check, when sourcing the wrong library version all kinds of weird
  # stuff can happen.
if [[ $1 != '"LIBRARY VERSION"' && ${DOCOPT_LIB_CHECK:-true} != 'false' ]]; then
  printf -- "cat <<'EOM' >&2\nThe version of the included docopt library (%s) \
does not match the version of the invoking docopt parser (%s)\nEOM\nexit 70\n" \
    '"LIBRARY VERSION"' "$1"
  exit 70
fi
}

parse() {
  # $DOC check. Makes sure that the replaced values of the placeholders in
  # docopt() are up-to-date
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

  # The AST nodes are indexed. To simplify, the code leaf nodes come first.
  # This allows us to reuse that index in the options array.
  # This also means that the root node isn't 0, so we need to pass that around.
  local root_idx=$1
  # All remaining arguments are actual parameters to the program
  shift

  #
  # PARSING STRATEGY
  #
  # Since options can be specified anywhere in the invocation, we cannot simply
  # traverse the generated AST and expect everything to be in its proper place.
  # Additionally, an option with an argument can be one or two words
  # (--long ARG vs. --long=ARG, or -a ARG vs. -aARG), while multiple short
  # options can be a single word (-a -b -c vs. -abc).
  # That is why we do a little pre-parsing of $argv by constructing the "parsed"
  # array. The array contains one parameter value per entry.
  # Each entry is prefixed, with either 'a:', meaning it's a non-option,
  # or with an index pointing at the option in the options array.
  # Example:
  # Usage: prog -s --val=OPTARG command ARG
  # $ prog command --val=optval "arg val" -s
  # -> (a:command 1:optval a:"arg val" 2:true)
  # It's basically a normalized version of $argv.

  # Global params array
  params=()
  # Global continuation array, the nodes that remain to be matched.
  # See BACKTRACKING below.
  continuation=()
  # Global assignments array, queued up by the leaves when they match.
  # The values they assign are kept in a separate array so we don't have to
  # quote them.
  assignments=()
  values=()

  # Parse argv one word at a time by examining index 0 and then unshifting
  # every parsed word (argv=("${argv[@]:1}"))
  local argv=("$@") arg i o
  while [[ ${#argv[@]} -gt 0 ]]; do
    if [[ ${argv[0]} = "--" ]]; then
      # No more options allowed.
      # Parse everything from here on out as commands or arguments. Then break.
      for arg in "${argv[@]}"; do
        params+=("a:$arg")
      done
      break
    elif [[ ${argv[0]} = --* ]]; then
      # Parse long
      local long=${argv[0]%%=*}
      # Bail early if it's a built-in option
      if ${DOCOPT_ADD_HELP:-true} && [[ $long = "--help" ]]; then
        # shellcheck disable=SC2154
        stdout "$trimmed_doc"
        _return 0
      elif [[ ${DOCOPT_PROGRAM_VERSION:-false} != 'false' && $long = "--version" ]]; then
        stdout "$DOCOPT_PROGRAM_VERSION"
        _return 0
      fi
      # Try matching the full long option first
      local similar=() match=false
      i=0
      # When used as a library, $options is defined in the sourcing scope
      # shellcheck disable=2154
      for o in "${options[@]}"; do
        if [[ $o = *" $long "? ]]; then
          similar+=("$long")
          match=$i
          break
        fi
        : $((i++))
      done
      if [[ $match = false ]]; then
        # No exact match was found, check for a prefix match.
        # I'm not a big fan of allowing users to shorten long options, but it's
        # part of the docopt spec (and presumably POSIX), so we implement it.
        i=0
        for o in "${options[@]}"; do
          if [[ $o = *" $long"*? ]]; then
            local long_match=${o#* }
            similar+=("${long_match% *}")
            match=$i
          fi
          : $((i++))
        done
      fi
      if [[ ${#similar[@]} -gt 1 ]]; then
        # ambiguous prefix found (e.g. --l matches the options --lat and --long)
        error "${long} is not a unique prefix: ${similar[*]}?"
      elif [[ ${#similar[@]} -lt 1 ]]; then
        # No match found
        error
      else
        # Match found
        if [[ ${options[$match]} = *0 ]]; then
          # Option does not accept an argument
          if [[ ${argv[0]} = *=* ]]; then
            local long_match=${o#* }
            error "${long_match% *} must not have an argument"
          else
            # Add option as a switch
            params+=("$match:true")
            # Unshift the param from argv
            argv=("${argv[@]:1}")
          fi
        else
          if [[ ${argv[0]} = *=* ]]; then
            # --long=ARG given, add to params and unshift param
            params+=("$match:${argv[0]#*=}")
            argv=("${argv[@]:1}")
          else
            if [[ ${#argv[@]} -le 1 || ${argv[1]} = '--' ]]; then
              error "${long} requires argument"
            fi
            # --long ARG given, add to params and unshift both params
            params+=("$match:${argv[1]}")
            argv=("${argv[@]:2}")
          fi
        fi
      fi
    elif [[ ${argv[0]} = -* && ${argv[0]} != "-" ]]; then
      # Parse shorts
      # We need to parse `-a` as well as `-abc'
      local remaining=${argv[0]#-}
      while [[ -n $remaining ]]; do
        # Parse one short at a time
        local short="-${remaining:0:1}"
        # Bail early if it's a built-in option
        if ${DOCOPT_ADD_HELP:-true} && [[ $short = "-h" ]]; then
          # shellcheck disable=SC2154
          stdout "$trimmed_doc"
          _return 0
        fi
        local matched=false
        # Unshift current short from list of remaining shorts
        remaining="${remaining:1}"
        i=0
        for o in "${options[@]}"; do
          if [[ $o = "$short "* ]]; then
            # Match found
            if [[ $o = *1 ]]; then
              # Option takes an argument
              if [[ $remaining = '' ]]; then
                # The next param is the argument
                if [[ ${#argv[@]} -le 1 || ${argv[1]} = '--' ]]; then
                  error "${short} requires argument"
                fi
                # Add param to params and unshift the next param
                params+=("$i:${argv[1]}")
                # This is not the actual value param but rather the shortlist
                # param. The value param will be unshifted at the end of the
                # shortlist loop.
                argv=("${argv[@]:1}")
                # break out of the shortlist parsing loop, we're done
                break 2
              else
                # The entire remaining part of the shortlist is the argument
                params+=("$i:$remaining")
                # break out of the shortlist parsing loop, we're done
                break 2
              fi
            else
              # Option does not take an argument, add to params
              params+=("$i:true")
              matched=true
              break
            fi
          fi
          : $((i++))
        done
        # No match found
        $matched || error
      done
      # Unshift the param
      argv=("${argv[@]:1}")
    elif ${DOCOPT_OPTIONS_FIRST:-false}; then
      # First non-option encountered and all options must be specified first.
      # Parse everything from here on out as commands or arguments. Then break.
      for arg in "${argv[@]}"; do
        params+=("a:$arg")
      done
      break
    else
      # Normal argument or command given, unshift to params and continue loop
      params+=("a:${argv[0]}")
      argv=("${argv[@]:1}")
    fi
  done

  # Run through the parsing tree, fail if not all params could be parsed.
  if ! "node_$root_idx" || [ ${#params[@]} -gt 0 ]; then
    error
  fi
  # Everything matched, set the variables
  for ((i=0; i<${#assignments[@]}; i++)); do
    eval "${assignments[$i]}"
  done
  return 0
}

#
# BACKTRACKING
#
# Matching each node greedily is not always enough. Consider the following:
#   Usage: prog [A] B
# AST:
#   <Sequence>
#     <Optional>
#       Argument: A
#     Argument: B
# Invocation:
#   $ prog x
# If [A] simply consumes "x", B has nothing left to match and parsing fails.
# So instead every node only succeeds if the nodes that come after it match as
# well. When they don't, the node tries something else (e.g. skipping A) before
# giving up.
# The nodes that come after are kept in the global $continuation array.
# A node prepends its subtree to it and calls match_continuation(), which
# removes the first entry and matches it. Apart from node indices, the array
# can contain:
# * ?IDX: An optional node, we try matching it first and then try skipping it
# * !: Stop and succeed regardless of the remaining params, see repeatable()
# Since a node can't know whether the parse succeeds until everything after it
# has matched, leaves can't set any variables right away. Instead they queue
# up assignments, which parse() evaluates once the entire AST has matched.

match_continuation() {
  if [[ ${continuation[0]} = '!' ]]; then
    return 0
  elif [[ ${#continuation[@]} -eq 0 ]]; then
    # Nothing left to match, succeed if all params have been consumed
    [[ ${#params[@]} -eq 0 ]]
    return $?
  fi
  local node_idx=${continuation[0]} rest=("${continuation[@]:1}")
  if [[ $node_idx = \?* ]]; then
    # Optional node, try matching it first (${node_idx#?} strips the "?")
    continuation=("${node_idx#?}" "${rest[@]}")
    match_continuation && return 0
    # Then try skipping it
    continuation=("${rest[@]}")
    match_continuation && return 0
  else
    continuation=("${rest[@]}")
    "node_$node_idx" && return 0
  fi
  continuation=("$node_idx" "${rest[@]}")
  return 1
}

sequence() {
  local initial_continuation=("${continuation[@]}")
  continuation=("$@" "${continuation[@]}")
  match_continuation && return 0
  continuation=("${initial_continuation[@]}")
  return 1
}

choice() {
  local initial_continuation=("${continuation[@]}") node_idx
  # Try the subtrees in order, the first one that leads to a match wins
  for node_idx in "$@"; do
    continuation=("$node_idx" "${initial_continuation[@]}")
    match_continuation && return 0
  done
  continuation=("${initial_continuation[@]}")
  return 1
}

optional() {
  local initial_continuation=("${continuation[@]}") optionals=() node_idx
  # Each subtree is optional on its own
  for node_idx in "$@"; do
    optionals+=("?$node_idx")
  done
  continuation=("${optionals[@]}" "${continuation[@]}")
  match_continuation && return 0
  continuation=("${initial_continuation[@]}")
  return 1
}

repeatable() {
  # Every consumed param adds frames to the call stack and bash segfaults after
  # a few thousand of them. So instead of recursing once per repetition, we
  # match as many repetitions as possible in a loop, each one on its own
  # (that's what the "!" is for).
  # Only the last repetition is matched together with the continuation. If that
  # fails, we try again with one repetition less, rematching the ones before it
  # from scratch. The downside is that all but the last repetition only use
  # their first match, not necessarily one that lets the continuation match.
  local initial_continuation=("${continuation[@]}")
  local initial_params=("${params[@]}") initial_count=${#assignments[@]}
  local before_params before_count last_params=() last_count count=0 i
  while true; do
    before_params=("${params[@]}")
    before_count=${#assignments[@]}
    continuation=("$1" '!')
    match_continuation || break
    : $((count++))
    last_params=("${before_params[@]}")
    last_count=$before_count
    # Nothing was consumed, so stop looping.
    # This happens when an optional param can be repeated.
    [[ ${#before_params[@]} -eq ${#params[@]} ]] && break
  done
  while [[ $count -gt 0 ]]; do
    # Rewind to before the last repetition and match it with the continuation
    params=("${last_params[@]}")
    assignments=("${assignments[@]:0:$last_count}")
    values=("${values[@]:0:$last_count}")
    continuation=("$1" "${initial_continuation[@]}")
    match_continuation && return 0
    # Rematch one repetition less
    : $((count--))
    params=("${initial_params[@]}")
    assignments=("${assignments[@]:0:$initial_count}")
    values=("${values[@]:0:$initial_count}")
    for ((i=1; i<count; i++)); do
      continuation=("$1" '!')
      match_continuation
    done
    last_params=("${params[@]}")
    last_count=${#assignments[@]}
  done
  params=("${initial_params[@]}")
  assignments=("${assignments[@]:0:$initial_count}")
  values=("${values[@]:0:$initial_count}")
  continuation=("${initial_continuation[@]}")
  return 1
}

# Signature: $param_idx $assignment $value
# Removes the matched param, queues its assignment and matches the continuation.
# Undoes all of that if the continuation does not match.
consume() {
  local initial_params=("${params[@]}") initial_count=${#assignments[@]}
  params=("${params[@]:0:$1}" "${params[@]:(($1+1))}")
  assignments+=("$2")
  values+=("$3")
  match_continuation && return 0
  params=("${initial_params[@]}")
  assignments=("${assignments[@]:0:$initial_count}")
  values=("${values[@]:0:$initial_count}")
  return 1
}

#
# LEAF PARSING
#
# We only need two functions for parsing any leaf. A leaf can be:
# * command
# * -- (argument separator)
# * ARGUMENT
# * --option
# * --option-with=ARGUMENT
# We can group these into:
# switches (command, --, --option) and
# values (ARGUMENT, --option-with=ARGUMENT).
# Both only consider the first param that matches. Once it is consumed, the
# rest of the AST is matched through the continuation (see BACKTRACKING).
# For a better understanding, consider the following program:
#   Usage: prog ARG (-a|-b)
# AST:
#   <Sequence>
#     Argument: ARG
#     <Choice>
#       -a
#       -b
# bash version:
#   node_4(){ sequence 2 3; }
#     node_2(){ value ARG a; }
#     node_3(){ choice 0 1; }
#       node_0(){ switch _a 0; }
#       node_1(){ switch _b 1; }
# Invocation:
#   $ prog -a X
# params=(0:true a:X)
# If we invoked it the other way around, one would expect this to fail, because
# sequence would expect to get the argument ARG and then the <Choice>.
#
# However, the behavior and interaction between the two leaf parsers ensures
# that we succeed:
# When parsing the sequence, we start with node_2 which expects the argument.
# It succeeds because -a is an option and therefore it's skipped.
# Then the argument is found as the second entry in $params.
# That entry is now removed from $params.
# Then we parse the choice with node_3, which expects -a or -b.
# The only remaining entry in $params "0:true"
# So all we have now is the remaining "-a", which is then successfully parsed.

# Signature: $var_name $params_prefix $multiple
# Where $params_prefix in the case of an option is the index
# and in the case of a command is the full command prefixed with "a:"
switch() {
  # Run though remaining params and check if there is an argument-less option,
  # a command, or argument separator in there
  local i param
  for i in "${!params[@]}"; do
    local param=${params[$i]}
    if [[ $param = "$2" || $param = "$2":* ]]; then
      # Name of the option/command matches, consume the param
      if [[ $3 = true ]]; then
        # Switch is repeatable, increase a counter
        consume "$i" "var_$1=\$((var_$1+1))" && return 0
      else
        # Switch is not repeatable, set to true
        consume "$i" "var_$1=true" && return 0
      fi
      # The rest of the AST did not match
      return 1
    elif [[ $param = a:* && $2 = a:* ]]; then
      # Fail if we were to parse a non-option and we encountered a non-option
      # where the name doesn't match
      return 1
    fi
  done
  # No switches left, fail
  return 1
}

# Signature: $var_name $params_prefix $multiple
# Where $params_prefix in the case of an option is the index
# and in the case of an argument is just "a"
value() {
  # Run though remaining params and check if there is an argument or an option
  # with an argument in there
  local i param
  for i in "${!params[@]}"; do
    local param=${params[$i]}
    if [[ $param = "$2":* ]]; then
      # Argument or option matches, consume the param.
      # The assignment refers to the value by its index in $values
      local value_ref="\${values[${#values[@]}]}"
      if [[ $3 = true ]]; then
        # Value is repeatable, add it to the array
        consume "$i" "var_$1+=(\"$value_ref\")" "${param#*:}" && return 0
      else
        # Value is not repeatable, set the value
        consume "$i" "var_$1=$value_ref" "${param#*:}" && return 0
      fi
      # The rest of the AST did not match
      return 1
    fi
    # We don't fail here like we do in switch() if we were to find a non-option.
    # This is because an ARGUMENT matches anything that isn't an option.
    # So when the above `if' doesn't match, it's because we encountered an
    # option.
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

