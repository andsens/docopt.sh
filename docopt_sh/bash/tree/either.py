from .. import Function


class Either(Function):
  def __init__(self, settings):
    super(Either, self).__init__(settings, 'either')

  @property
  def body(self):
    body = '''
local init_lft=("${_lft[@]}")
local bm
local prev_best
local pattern
local _do_unset_tm=true
$_do_tm && _do_unset_tm=false
_do_tm=true
for pattern in "$@"; do
  if $pattern; then
    if [[ -z $prev_best || ${#_lft[@]} -lt $prev_best ]]; then
      bm=$pattern
      prev_best=${#_lft[@]}
    fi
  fi
  _lft=("${init_lft[@]}")
done
$_do_unset_tm && _do_tm=false
if [[ -n $bm ]]; then
  $bm
  return 0
fi
_lft=("${init_lft[@]}")
return 1
'''
    return body
