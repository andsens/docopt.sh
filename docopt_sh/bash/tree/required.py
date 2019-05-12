from .. import Function


class Required(Function):
  def __init__(self, settings):
    super(Required, self).__init__(settings, '_do_req')

  @property
  def body(self):
    body = '''
local init_lft=("${_lft[@]}")
local p
local unset_tm=true
$_do_tm && unset_tm=false
_do_tm=true
for p in "$@"; do
  if ! "_do$p"; then
    _lft=("${init_lft[@]}")
    $unset_tm && _do_tm=false
    return 1
  fi
done
if $unset_tm; then
  _do_tm=false
  _lft=("${init_lft[@]}")
  for p in "$@"; do
    "_do$p"
  done
fi
return 0
'''
    return body
