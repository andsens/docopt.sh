from .. import Function


class OneOrMore(Function):

  name = '_do_oom'

  def __init__(self, settings):
    super(OneOrMore, self).__init__(settings, OneOrMore.name)

  @property
  def body(self):
    body = '''
local i=0
local prev=${#_lft[@]}
while "_do$1"; do
  ((i++))
  [[ $prev -eq ${#_lft[@]} ]] && break
  prev=${#_lft[@]}
done
if [[ $i -ge 1 ]]; then
  return 0
fi
return 1
'''
    return body
