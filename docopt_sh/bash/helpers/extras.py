from .. import Function


class Extras(Function):

  def __init__(self, settings):
    super(Extras, self).__init__(settings, 'extras')

  def include(self):
    return self.settings.add_help or self.settings.add_version

  @property
  def body(self):
    body = ''
    if self.settings.add_help:
      body += '''
for idx in "${parsed_params[@]}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${options_short[$idx]} == "-h" || ${options_long[$idx]} == "--help" ]]; then
    help
    exit 0
  fi
done
'''
    if self.settings.add_version:
      body += '''
for idx in "${parsed_params[@]}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${options_long[$idx]} == "--version" ]]; then
    printf "%s\\n" "$version"
    exit 0
  fi
done
'''
    return body
