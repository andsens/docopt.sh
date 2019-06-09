from .doc_ast import Option, Command, Required, Optional, OptionsShortcut, OneOrMore, Either
from .bash import Function, bash_variable_name, bash_ifs_value

helper_map = {
  Required: 'docopt_required',
  Optional: 'docopt_optional',
  OptionsShortcut: 'docopt_optional',
  OneOrMore: 'docopt_oneormore',
  Either: 'docopt_either',
}


class Node(Function):

  def __init__(self, pattern, idx):
    self.type = type(pattern)
    self.idx = idx
    super(Node, self).__init__('docopt_node_' + str(idx))


class BranchNode(Node):

  def __init__(self, pattern, idx, function_map):
    super(BranchNode, self).__init__(pattern, idx)
    self.helper_name = helper_map[self.type]
    self.child_indexes = map(lambda child: function_map[child].idx, pattern.children)

  @property
  def body(self):
    # minify arg list by only specifying node idx
    body = ' '.join([self.helper_name] + list(map(str, self.child_indexes)))
    return '  ' + body


class LeafNode(Node):

  def __init__(self, pattern, idx, name_prefix):
    super(LeafNode, self).__init__(pattern, idx)
    self.default_value = pattern.value
    self.pattern = pattern
    if self.type is Option:
      self.helper_name = 'docopt_switch' if type(self.default_value) in [bool, int] else 'docopt_value'
      self.needle = idx
    elif self.type is Command:
      self.helper_name = 'docopt_command'
      self.needle = pattern.name
    else:
      self.helper_name = 'docopt_value'
      self.needle = 'a'
    self.multiple = type(self.default_value) in [list, int]
    self.variable_name = bash_variable_name(pattern.name, name_prefix)

  @property
  def body(self):
    args = [self.variable_name, bash_ifs_value(self.needle)]
    if self.multiple:
      args.append(bash_ifs_value(self.multiple))
    if self.helper_name == 'docopt_command' and args[0] == args[1] and len(args) == 2:
      args = [args[0]]
    body = ' '.join([self.helper_name] + args)
    return '  ' + body
