#!/usr/bin/env bash

# def docopt(doc, argv=None, help=True, version=None, options_first=False):
test() {
  export debug=false
  test=false
  bashprint=false
  if [[ $1 == '-d' ]]; then
    debug=true
    shift
  elif [[ $1 == '-dd' ]]; then
    debug=true
    bashprint=true
    shift
  elif [[ $1 == '-t' ]]; then
    test=true
    shift
  fi
  local program=$1
  shift
  local doc
  if [[ $program == '-' ]]; then
    doc=$(cat)
  else
    doc=$(cat "usage/$program.txt")
  fi
  # local help=true
  # local version=''
  options_first=false
  if $debug; then
    printf "#!/usr/bin/env bash\n\n" > parser.sh
    if ! ./docopt_sh.py <<<"$doc" >> parser.sh; then
      return 1
    fi
    source parser.sh
  else
    eval "$(./docopt_sh.py <<<"$doc")"
  fi

  docopt "$@"
  ok=$?
  if $debug; then
    printf "\n"
    debug_var "options_short" "${options_short[@]}"
    debug_var "options_long" "${options_long[@]}"
    debug_var "parsed_params" "${parsed_params[@]}"
  fi
  if [[ $ok -eq 0 ]]; then
    if $test; then
      for var in "${param_names[@]}"; do declare -p "$var"; done
    else
      for var in "${param_names[@]}"; do
        if declare -p "$var" | grep -q 'declare -a'; then
          printf -- "%s" "$var"
          local size
          # shellcheck disable=SC1087
          size="$(eval "echo \${#$var[@]}")"
          $debug && printf -- " (%d)" "$size"
          printf ": ("
          local i=0
          while [[ $i -lt $size ]]; do
            printf -- "'%s'" "$(eval "echo \${$var[$i]}")"
            ((i++))
            [[ $i -ne $size ]] && printf " "
          done
          printf ")\n"
        else
          debug_var "$var" "$(eval "echo \$$var")"
        fi
      done
    fi
  fi
  $debug && debug_var "left" "${left[@]}"
  return $ok
}

debug_var() {
  local varname=$1
  shift
  printf -- "%s" "$varname"
  if declare -p "$varname" | grep -q 'declare -a'; then
    printf -- " (%d): " "$#"
    printf -- "'%s' " "$@"
  else
    printf -- ": %s" "$1"
  fi
  printf "\n"
}

die() {
  # shellcheck disable=2059
  printf "$1\n" "$2" >&2
  exit 1
}

test "$@"
