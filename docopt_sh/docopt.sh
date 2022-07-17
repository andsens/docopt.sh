#!/usr/bin/env bash

docopt() {
  # This function will always be directly inlined in the script.
  # It contains all the specifics of $DOC, while the remaining functions
  # are generic. All strings with uppercase letters a placeholders.

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
  # the items space separated. The order matches the AST node numbering
  options=("OPTIONS")
  # This is the AST representing the parsed doc.
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
  local p=${DOCOPT_PREFIX:-''}

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

  # The AST nodes are indexed. To simplify the code leaf nodes come first.
  # This allows us to reuse that index in the options array.
  # This also means that the root node isn't 0, so we need to pass that around.
  local root_idx=$1
  # All remaining arguments are actual arguments to the program
  shift

  #
  # PARSING STRATEGY
  #
  # Since options can be specified anywhere in the invocation, we cannot simply
  # traverse the generated AST and expect everything to be in its proper place.
  # Additionaly, an option with an argument can be one or two arguments
  # (--long ARG vs. --long=ARG, or -a ARG vs. -aARG), while multiple short
  # options can be a single argument (-a -b -c vs. -abc).
  # That is why we do a little pre-parsing of $argv by constructing the "parsed"
  # array. The array contains one parameter value per entry.
  # Each entry is prefixed, with either 'a:', meaning it's a non-option,
  # or with an index pointing at the option in the options array.
  # Example:
  # Usage: prog -s --val=OPTARG command ARG
  # $ prog command --val=optval "arg val" -s
  # -> (a:command 1:optval a:"arg val" 2:true)
  # It's basically a normalized version of $argv.
  parsed=()
  # Array containing indices of the remaining unparsed params.
  # Initially filled with 0 through ${#parsed[@]}.
  # Parsers will remove indices on successful parsing
  left=()
  # Testing depth counter, when >0 nodes only check for potential matches.
  # When ==0 leafs will set the actual variable if a match is found.
  testdepth=0

  # unshift the parameters and parse them one param at a time
  local argv=("$@") arg i o
  while [[ ${#argv[@]} -gt 0 ]]; do
    if [[ ${argv[0]} = "--" ]]; then
      # No more options allowed.
      # Parse everything from here on out as commands or arguments. Then break.
      for arg in "${argv[@]}"; do
        parsed+=("a:$arg")
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
      for o in "${options[@]}"; do
        if [[ $o = *" $long "? ]]; then
          similar+=("$long")
          match=$i
          break
        fi
        : $((i++))
      done
      if [[ $match = false ]]; then
        # No exact match was found, check for a prefix match
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
            parsed+=("$match:true")
            # Unshift the param from argv
            argv=("${argv[@]:1}")
          fi
        else
          if [[ ${argv[0]} = *=* ]]; then
            # --long=ARG given, add to parsed and unshift param
            parsed+=("$match:${argv[0]#*=}")
            argv=("${argv[@]:1}")
          else
            if [[ ${#argv[@]} -le 1 || ${argv[1]} = '--' ]]; then
              error "${long} requires argument"
            fi
            # --long ARG given, add to parsed and unshift both params
            parsed+=("$match:${argv[1]}")
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
                # Add param to parsed and unshift the next param
                parsed+=("$i:${argv[1]}")
                # This is not the actual value param but rather the shortlist
                # param. The value param will be unshifted at the end of the
                # shortlist loop.
                argv=("${argv[@]:1}")
                # break out of the shortlist parsing loop, we're done
                break 2
              else
                # The entire remaining part of the shortlist is the argument
                parsed+=("$i:$remaining")
                # break out of the shortlist parsing loop, we're done
                break 2
              fi
            else
              # Option does not take an argument, add to parsed
              parsed+=("$i:true")
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
        parsed+=("a:$arg")
      done
      break
    else
      # Normal argument or command given, unshift to parsed and continue loop
      parsed+=("a:${argv[0]}")
      argv=("${argv[@]:1}")
    fi
  done

  # Populate the array of remaining indices to parse
  i=0
  while [[ $i -lt ${#parsed[@]} ]]; do
    left+=("$i")
    : $((i++))
  done

  # Run through the parsing tree, fail if not all params could be parsed.
  if ! "node_$root_idx" || [ ${#left[@]} -gt 0 ]; then
    error
  fi
  return 0
}

sequence() {
  local initial_left=("${left[@]}") node_idx
  # Increase testdepth, so we don't partially set variables and then fail
  : $((testdepth++))
  # Check if we can match the entire subtree
  for node_idx in "$@"; do
    if ! "node_$node_idx"; then
      # Unable to match the entire subtree, reset the remaining params
      left=("${initial_left[@]}")
      : $((testdepth--))
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
  local initial_left=("${left[@]}") best_match_idx match_count node_idx
  # Increase testdepth, so that we can test all subtrees without setting variables
  : $((testdepth++))
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
  local matched=false prev=${#left[@]}
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
# When either of these function parse options, they only return 1 when they have
# run through the complete list of parameters that are yet to parsed and no
# match was found.

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

