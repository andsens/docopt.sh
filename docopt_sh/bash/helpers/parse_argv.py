from .. import Function


class ParseArgv(Function):

  def __init__(self, settings):
    super(ParseArgv, self).__init__(settings, 'parse_argv')

  def __str__(self):
    script = '''
while [[ ${#argv[@]} -gt 0 ]]; do
  if [[ ${argv[0]} == "--" ]]; then
    for arg in "${argv[@]}"; do
      parsed_params+=('a')
      parsed_values+=("$arg")
    done
    return
  elif [[ ${argv[0]} = --* ]]; then
    parse_long
  elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then
    parse_shorts
'''
    if self.settings.options_first:
      script += '''
  else
    for arg in "${argv[@]}"; do
      parsed_params+=('a')
      parsed_values+=("$arg")
    done
    return
'''
    else:
      script += '''
  else
    parsed_params+=('a')
    parsed_values+=("${argv[0]}")
    argv=("${argv[@]:1}")
'''
    script += '''
  fi
done
'''
    return self.fn_wrap(script)
