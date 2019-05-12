from .. import Function


class Main(Function):
  def __init__(self, settings):
    super(Main, self).__init__(settings, 'docopt')

  def __str__(self):
    script = '''
type check &>/dev/null && check
setup "$@"
parse_argv
extras
local i=0
while [[ $i -lt ${#parsed_params[@]} ]]; do left+=("$i"); ((i++)); done
if ! root; then
  error
fi
type defaults &>/dev/null && defaults
if [[ ${#left[@]} -gt 0 ]]; then
  error
fi
type teardown &>/dev/null && teardown
return 0
'''
    return self.fn_wrap(script)
