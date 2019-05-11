from .. import Function, bash_variable_name, bash_variable_value


class Defaults(Function):
  def __init__(self, settings, sorted_params):
    super(Defaults, self).__init__(settings, 'defaults')
    self.sorted_params = sorted_params

  def include(self):
    return len(self.sorted_params) > 0

  def __str__(self):
    defaults = [
      "[[ -z ${{{name}+x}} ]] && {name}={default}".format(
        name=bash_variable_name(p.name, self.settings.name_prefix), default=bash_variable_value(p.value)
      )
      if type(p.value) is list else "{name}=${{{name}:-{default}}}".format(
        name=bash_variable_name(p.name, self.settings.name_prefix), default=bash_variable_value(p.value)
      )
      for p in self.sorted_params
    ]
    script = '\n'.join(defaults)
    return self.fn_wrap(script)
