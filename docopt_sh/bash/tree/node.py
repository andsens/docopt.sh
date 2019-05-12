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
    self.type = type(pattern)
    super(Node, self).__init__(settings, prefix_map[self.type] + str(idx))


class BranchNode(Node):

  def __init__(self, settings, pattern, idx, function_map):
    super(BranchNode, self).__init__(settings, pattern, idx)
    if self.type is OptionsShortcut:
      self.helper_name = 'optional'
    else:
      self.helper_name = pattern.__class__.__name__.lower()
    self.child_names = map(lambda child: function_map[child].name, pattern.children)

  @property
  def body(self):
    body = ' '.join([self.helper_name] + list(self.child_names))
    return body


class LeafNode(Node):

  def __init__(self, settings, pattern, idx):
    super(LeafNode, self).__init__(settings, pattern, idx)
    if self.type is Option:
      self.helper_name = '_switch' if type(pattern.value) in [bool, int] else '_value'
      self.needle = idx
    elif self.type is Command:
      self.helper_name = '_command'
      self.needle = pattern.name
    else:
      self.helper_name = '_value'
      self.needle = None
    self.variable_name = bash_variable_name(pattern.name, settings.name_prefix)
    self.multiple = type(pattern.value) in [list, int]

  @property
  def body(self):
    body = ' '.join([
      self.helper_name,
      self.variable_name,
      bash_ifs_value(self.multiple),
      bash_ifs_value(self.needle)
    ])
    return body
