from .. import Function


class Extras(Function):

  def __init__(self, add_help, no_version, version_present):
    super(Extras, self).__init__('extras')
    self.add_help = add_help
    self.add_version = not no_version and version_present

  def include(self):
    return self.add_help or self.add_version

  def __str__(self):
    script = ''
    if self.add_help:
      script += '''
for idx in "${parsed_params[@]}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${options_short[$idx]} == "-h" || ${options_long[$idx]} == "--help" ]]; then
    help
    exit 0
  fi
done
'''
    if self.add_version:
      script += '''
for idx in "${parsed_params[@]}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${options_long[$idx]} == "--version" ]]; then
    printf "%s\n" "$version"
    exit 0
  fi
done
'''
    return self.fn_wrap(script)
