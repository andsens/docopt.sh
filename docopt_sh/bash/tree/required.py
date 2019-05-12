from .. import Function


class Required(Function):
  def __init__(self, settings):
    super(Required, self).__init__(settings, 'required')

  @property
  def body(self):
    body = '''
local initial__lft=("${_lft[@]}")
local pattern
local _do_unset_tm=true
$_do_tm && _do_unset_tm=false
_do_tm=true
for pattern in "$@"; do
  if ! $pattern; then
    _lft=("${initial__lft[@]}")
    $_do_unset_tm && _do_tm=false
    return 1
  fi
done
if $_do_unset_tm; then
  _do_tm=false
  _lft=("${initial__lft[@]}")
  for pattern in "$@"; do $pattern; done
fi
return 0
'''
    return body
