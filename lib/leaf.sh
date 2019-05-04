#!/usr/bin/env bash

leaf() {
  $1 "$2"
#   pos, match = self.single_match(left)
  if ! $1 "$2"; then
    left=("${left_reset[@]}")
    unset_params "${params_set[@]:$reset_from}"
    return 1
  fi
  left_=(${left[@]:0:$pos})
  left_+=(${left[@]:((pos+1))})
#   left_ = left[:pos] + left[pos + 1:]
  for a in "${collected[@]}"; do
    if [[ ??? == $2 ]]; then
      same_name=???
      break
    fi
  done
#   same_name = [a for a in collected if a.name == self.name]
  if ???
#   if type(self.value) in (int, list):
  if ???
#     if type(self.value) is int:
      increment=1
#       increment = 1
    else
#     else:
      ???
#       increment = ([match.value] if type(match.value) is str
#              else match.value)
    if [[ -z $same_name ]]; then
#     if not same_name:
      ??? = increment
#       match.value = increment
      r_match=true
      r_left=(${left_[@]})
      r_collected=(${r_collected[@]})
      r_collected+=(match???)
      return
#       return True, left_, collected + [match]
    fi
    same_name???=((same_name??? + increment))
#     same_name[0].value += increment
    r_match=true
    r_left=(${left_[@]})
    r_collected=(${r_collected[@]})
    r_collected[???]=same_name
    return
#     return True, left_, collected
  fi
  r_match=true
  r_left=(${left_[@]})
  r_collected=(${r_collected[@]})
  r_collected+=(match???)
  return
#   return True, left_, collected + [match]
}
