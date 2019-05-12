from .. import Function, bash_variable_value


class Defaults(Function):
  def __init__(self, settings, leaf_nodes):
    super(Defaults, self).__init__(settings, '_do_def')
    self.leaf_nodes = leaf_nodes

  @property
  def body(self):
    defaults = []
    for node in self.leaf_nodes:
      if type(node.default_value) is list:
        tpl = "[[ -z ${{{name}+x}} ]] && {name}={default}"
      else:
        tpl = "{name}=${{{name}:-{default}}}"
      defaults.append(tpl.format(
        name=node.variable_name,
        default=bash_variable_value(node.default_value)
      ))
    body = '\n'.join(defaults)
    return body
