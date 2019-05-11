from .. import Function


class Extras(Function):

  def __init__(self, settings):
    super(Extras, self).__init__(settings, 'extras')

  def include(self):
    return self.settings.add_help or self.settings.add_version

  def __str__(self):
    script = ''
    if self.settings.add_help:
      script += '''
for idx in "${parsed_params[@]}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${options_short[$idx]} == "-h" || ${options_long[$idx]} == "--help" ]]; then
    help
    exit 0
  fi
done
'''
    if self.settings.add_version:
      script += '''
for idx in "${parsed_params[@]}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${options_long[$idx]} == "--version" ]]; then
    printf "%s\\n" "$version"
    exit 0
  fi
done
'''
    return self.fn_wrap(script)
