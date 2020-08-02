from .doc_ast import Option, Command, Required, Optional, OptionsShortcut, OneOrMore, Either
from .bash import Code, bash_variable_name, bash_variable_value, bash_ifs_value
from shlex import quote

helper_map = {
  Required: 'required',
  Optional: 'optional',
  OptionsShortcut: 'optional',
  OneOrMore: 'oneormore',
  Either: 'either',
}
helper_list = list(helper_map.values()) + [
  'switch',
  '_command',
  'value',
]


class Node(Code):

  def __init__(self, pattern, body, idx):
    self.pattern = pattern
    self.idx = idx
    code = '{name}(){{\n{body}\n}}\n'.format(
      name='node_' + str(idx),
      body=body,
    )
    super(Node, self).__init__(code)


class BranchNode(Node):

  def __init__(self, pattern, idx, node_map):
    # minify arg list by only specifying node idx
    child_indexes = map(lambda child: node_map[child].idx, pattern.children)
    self.helper_name = helper_map[type(pattern)]
    body = '  {helper} {args}'.format(
      helper=self.helper_name,
      args=' '.join(list(map(str, child_indexes))),
    )
    super(BranchNode, self).__init__(pattern, body, idx)


class LeafNode(Node):

  def __init__(self, pattern, idx):
    default_value = pattern.value
    if type(pattern) is Option:
      self.helper_name = 'switch' if type(default_value) in [bool, int] else 'value'
      needle = idx
    elif type(pattern) is Command:
      self.helper_name = '_command'
      needle = pattern.name
    else:  # type is Argument
      self.helper_name = 'value'
      needle = 'a'
    self.variable_name = bash_variable_name(pattern.name)

    args = [self.variable_name, bash_ifs_value(needle)]
    if type(default_value) in [list, int]:
      args.append(bash_ifs_value(True))
    elif self.helper_name == '_command' and args[0] == args[1]:
      args = [args[0]]
    body = '  {helper} {args}'.format(
      helper=self.helper_name,
      args=' '.join(args),
    )

    if type(default_value) is list:
      assignment1 = '{name}=("${{{docopt_name}[@]}}")'.format(
        name=self.variable_name,
        docopt_name='var_' + self.variable_name
      )
      assignment2 = '{name}={default}'.format(
        name=self.variable_name,
        default=bash_variable_value(default_value)
      )
      self.default_assignment = (
        'if declare -p {docopt_name} >/dev/null 2>&1; then\n'
        '  eval "${{prefix}}"{assignment1}\n'
        'else\n'
        '  eval "${{prefix}}"{assignment2}\n'
        'fi'
      ).format(
        docopt_name='var_' + self.variable_name,
        assignment1=quote(assignment1),
        assignment2=quote(assignment2)
      )
    else:
      assignment = '{name}=${{{docopt_name}:-{default}}}'.format(
        name=self.variable_name,
        docopt_name='var_' + self.variable_name,
        default=bash_variable_value(default_value)
      )
      self.default_assignment = (
        'eval "${{prefix}}"{assignment}'
      ).format(
        assignment=quote(assignment)
      )
    super(LeafNode, self).__init__(pattern, body, idx)
