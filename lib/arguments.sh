#!/usr/bin/env bash

_arguments() {
  for l in "${left[@]}"; do
    if [[ ${parsed_params[$l]} == 'a' ]]; then
      eval "$(printf -- "%s=%s" "${parsed_values[$l]}")"
      return 0
    fi
  done
  return 1
}

#   argument()
    def single_match(self, left):
#       local name=$1
#       local left=(${p_left[@]})
#       pos=0
#       for l in "${left[@]}"; do
        for n, pattern in enumerate(left):
#           ???
            if type(pattern) is Argument:
#                   r_pos=$pos
#                   r_name=$?????
#                   r_res=$?????
#                   return
                return n, Argument(self.name, pattern.value)
#           ((pos++))
#           fi
#       done
#       r_pos=false
#       r_res=false
#       return
        return None, None
#   }
