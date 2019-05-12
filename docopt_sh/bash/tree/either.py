from .. import Function


class Either(Function):
  def __init__(self, settings):
    super(Either, self).__init__(settings, '_do_eith')

  @property
  def body(self):
    body = '''
local i_lft=("${_lft[@]}")
local best
local p_lft
local p
local unset_tm=true
$_do_tm && unset_tm=false
_do_tm=true
for p in "$@"; do
  if "_do$p"; then
    if [[ -z $p_lft || ${#_lft[@]} -lt $p_lft ]]; then
      best=_do$p
      p_lft=${#_lft[@]}
    fi
  fi
  _lft=("${i_lft[@]}")
done
$unset_tm && _do_tm=false
if [[ -n $best ]]; then
  $best
  return 0
fi
_lft=("${i_lft[@]}")
return 1
'''
    return body
