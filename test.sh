#!/usr/bin/env bash

# def docopt(doc, argv=None, help=True, version=None, options_first=False):
test() {
  debug=false
  if [[ $1 == '-d' ]]; then
    debug=true
    shift
  fi
  local program=$1
  shift
  local doc
  doc=$(cat "usage/$program.txt")
  # local help=true
  # local version=''
  options_first=false
  printf "#!/usr/bin/env bash\n\n" > parser.sh
  if ! ./docopt.py <<<"$doc" >> parser.sh; then
    return 1
  fi
  source parser.sh

  if docopt "$@"; then
    :
  fi
  printf "\n"
  debug_var "options_short" "${options_short[@]}"
  debug_var "options_long" "${options_long[@]}"
  debug_var "parsed_params" "${parsed_params[@]}"
  debug_var "parsed_values" "${parsed_values[@]}"
  for var in "${param_names[@]}"; do
    if declare -p "$var" | grep -q 'declare -a'; then
      #shellcheck disable=1087
      debug_var "$var" "$(eval "echo \${$var[*]}")"
    else
      debug_var "$var" "$(eval "echo \$$var")"
    fi
  done
  debug_var "left" "${left[@]}"
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
