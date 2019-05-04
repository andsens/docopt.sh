#!/usr/bin/env bash

# def docopt(doc, argv=None, help=True, version=None, options_first=False):
test() {
  local program=$1
  shift
  local doc
  doc=$(cat "usage/$program.txt")
  # local help=true
  # local version=''
  options_first=false
  local out
  printf "#!/usr/bin/env bash\n\n" > parser.sh
  ./docopt.py <<<"$doc" >> parser.sh
  source parser.sh

  if docopt "$@"; then
    :
  fi
    debug_var "options_short" "${options_short[@]}"
    debug_var "options_long" "${options_long[@]}"
    debug_var "parsed_params" "${parsed_params[@]}"
    debug_var "parsed_values" "${parsed_values[@]}"
  for var in "${param_names[@]}"; do
    debug_var "$var" "$(eval "echo \$$var")"
  done
  debug_var "left" "${left[@]}"
}

debug_var() {
  local varname=$1
  shift
  printf -- "%s" "$varname"
  if [[ $# -eq 1 ]]; then
    printf -- ": %s" "$1"
  else
    printf -- " (%d): " "$#"
    printf -- "'%s' " "$@"
  fi
  printf "\n"
}

die() {
  # shellcheck disable=2059
  printf "$1\n" "$2" >&2
  exit 1
}

test "$@"
