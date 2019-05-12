from .. import Function, bash_variable_name, bash_ifs_value
from ...doc import Option, Command, Argument, Required, Optional, OptionsShortcut, OneOrMore, Either

helper_map = {
  Required: '_do_req',
  Optional: '_do_opt',
  OptionsShortcut: '_do_opt',
  OneOrMore: '_do_oom',
  Either: '_do_eith',
}


class Node(Function):

  def __init__(self, settings, pattern, idx):
    self.type = type(pattern)
    self.idx = idx
    super(Node, self).__init__(settings, '_do' + str(idx))


class BranchNode(Node):

  def __init__(self, settings, pattern, idx, function_map):
    super(BranchNode, self).__init__(settings, pattern, idx)
    self.helper_name = helper_map[self.type]
    self.child_indexes = map(lambda child: function_map[child].idx, pattern.children)

  @property
  def body(self):
    # minimize arg list by only specifying node idx
    body = ' '.join([self.helper_name] + list(map(str, self.child_indexes)))
    return body


class LeafNode(Node):

  def __init__(self, settings, pattern, idx):
    super(LeafNode, self).__init__(settings, pattern, idx)
    self.default_value = pattern.value
    self.pattern = pattern
    if self.type is Option:
      self.helper_name = '_do_sw' if type(self.default_value) in [bool, int] else '_do_val'
      self.needle = idx
    elif self.type is Command:
      self.helper_name = '_do_cmd'
      self.needle = pattern.name
    else:
      self.helper_name = '_do_val'
      self.needle = 'a'
    self.multiple = type(self.default_value) in [list, int]
    self.variable_name = bash_variable_name(pattern.name, settings.name_prefix)

  @property
  def body(self):
    args = [self.variable_name, bash_ifs_value(self.needle)]
    if self.multiple:
      args.append(bash_ifs_value(self.multiple))
    if self.helper_name == '_do_cmd' and args[0] == args[1] and len(args) == 2:
      args = [args[0]]
    body = ' '.join([self.helper_name] + args)
    return body
