from .. import tree
from .. import Function, bash_variable_name, bash_ifs_value
from ...doc import Option, Command


class Node(Function):

  def __init__(self, settings, pattern, idx):
    self.type = type(pattern)
    self.idx = idx
    super(Node, self).__init__(settings, 'docopt_node_' + str(idx))


class BranchNode(Node):

  def __init__(self, settings, pattern, idx, function_map):
    super(BranchNode, self).__init__(settings, pattern, idx)
    from . import helper_map
    self.helper_name = helper_map[self.type].name
    self.child_names = map(lambda child: function_map[child].name, pattern.children)

  @property
  def body(self):
    # minify arg list by only specifying node idx
    body = ' '.join([self.helper_name] + list(map(str, self.child_names)))
    return body


class LeafNode(Node):

  def __init__(self, settings, pattern, idx):
    super(LeafNode, self).__init__(settings, pattern, idx)
    from . import helper_map
    self.default_value = pattern.value
    self.pattern = pattern
    if self.type is Option:
      self.helper_name = tree.Switch.name if type(self.default_value) in [bool, int] else tree.Value.name
      self.needle = idx
    elif self.type is Command:
      self.helper_name = tree.Command.name
      self.needle = pattern.name
    else:
      self.helper_name = tree.Value.name
      self.needle = 'a'
    self.multiple = type(self.default_value) in [list, int]
    self.variable_name = bash_variable_name(pattern.name, settings.name_prefix)

  @property
  def body(self):
    args = [self.variable_name, bash_ifs_value(self.needle)]
    if self.multiple:
      args.append(bash_ifs_value(self.multiple))
    if self.helper_name == tree.Command.name and args[0] == args[1] and len(args) == 2:
      args = [args[0]]
    body = ' '.join([self.helper_name] + args)
    return body
