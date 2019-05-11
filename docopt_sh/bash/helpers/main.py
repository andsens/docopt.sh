from .. import Function


class Main(Function):
  def __init__(self, settings, root_fn):
    super(Main, self).__init__(settings, 'docopt')
    self.root_fn = root_fn

  def __str__(self):
    script = '''
type check &>/dev/null && check
setup "$@"
parse_argv
extras
local i=0
while [[ $i -lt ${{#parsed_params[@]}} ]]; do left+=("$i"); ((i++)); done
if ! {root_fn}; then
  help
  exit 1
fi
type defaults &>/dev/null && defaults
if [[ ${{#left[@]}} -gt 0 ]]; then
  help
  exit 1
fi
type teardown &>/dev/null && teardown
return 0
'''.format(root_fn=self.root_fn)
    return self.fn_wrap(script)
