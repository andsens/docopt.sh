from .. import Function


class OneOrMore(Function):

  name = 'docopt_oneormore'

  def __init__(self, settings):
    super(OneOrMore, self).__init__(settings, OneOrMore.name)

  @property
  def body(self):
    body = '''
local i=0
local prev=${#docopt_left[@]}
while "$1"; do
  ((i++))
  [[ $prev -eq ${#docopt_left[@]} ]] && break
  prev=${#docopt_left[@]}
done
if [[ $i -ge 1 ]]; then
  return 0
fi
return 1
'''
    return body
