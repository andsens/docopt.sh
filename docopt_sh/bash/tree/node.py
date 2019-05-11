from .. import Function, bash_variable_name, bash_ifs_value
from ...doc import Option, Command, Argument, Required, Optional, OptionsShortcut, OneOrMore, Either

prefix_map = {
  Option: 'arg',
  Command: 'cmd',
  Argument: 'opt',
  Required: 'req',
  Optional: 'optional',
  OptionsShortcut: 'options',
  OneOrMore: 'oneormore',
  Either: 'either',
}


class Node(Function):

  def __init__(self, settings, pattern, idx):
    name = prefix_map[type(pattern)] + str(idx)
    super(Node, self).__init__(settings, name)


class BranchNode(Node):

  def __init__(self, settings, pattern, idx, function_map):
    if type(pattern) is OptionsShortcut:
      self.helper_name = 'optional'
    else:
      self.helper_name = pattern.__class__.__name__.lower()
    self.child_names = map(lambda child: function_map[child].name, pattern.children)
    super(BranchNode, self).__init__(settings, pattern, idx)

  def __str__(self):
    script = ' '.join([self.helper_name] + list(self.child_names))
    return self.fn_wrap(script)


class LeafNode(Node):

  def __init__(self, settings, pattern, idx):
    if type(pattern) is Option:
      self.helper_name = '_switch' if type(pattern.value) in [bool, int] else '_value'
      self.needle = idx
    elif type(pattern) is Command:
      self.helper_name = '_command'
      self.needle = pattern.name
    else:
      self.helper_name = '_value'
      self.needle = None
    self.variable_name = bash_variable_name(pattern.name, settings.name_prefix)
    self.multiple = type(pattern.value) in [list, int]
    super(LeafNode, self).__init__(settings, pattern, idx)

  def __str__(self):
    script = ' '.join([
      self.helper_name,
      self.variable_name,
      bash_ifs_value(self.multiple),
      bash_ifs_value(self.needle)
    ])
    return self.fn_wrap(script)
