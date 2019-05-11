from .. import Function, bash_variable_name, bash_ifs_value
from ...doc import Option


class Setup(Function):

  def __init__(self, settings, sorted_params):
    super(Setup, self).__init__(settings, 'setup')
    self.sorted_params = sorted_params

  def __str__(self):
    sorted_options = [o for o in self.sorted_params if type(o) is Option]
    script = '''
argv=("$@")
options_short=({options_short})
options_long=({options_long})
options_argcount=({options_argcount})
param_names=({param_names})
parsed_params=()
parsed_values=()
left=()
test_match=false
for var in "${{param_names[@]}}"; do unset "$var"; done
'''.format(
      options_short=' '.join([bash_ifs_value(o.short) for o in sorted_options]),
      options_long=' '.join([bash_ifs_value(o.long) for o in sorted_options]),
      options_argcount=' '.join([bash_ifs_value(o.argcount) for o in sorted_options]),
      param_names=' '.join([bash_variable_name(p.name, self.settings.name_prefix) for p in self.sorted_params]),
    )
    return self.fn_wrap(script)
