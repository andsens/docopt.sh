from .doc_ast import Option, Command, Required, Optional, OptionsShortcut, OneOrMore, Either
from .bash import Code, bash_variable_name, bash_variable_value, bash_ifs_value

helper_map = {
  Required: 'docopt_required',
  Optional: 'docopt_optional',
  OptionsShortcut: 'docopt_optional',
  OneOrMore: 'docopt_oneormore',
  Either: 'docopt_either',
}


class Node(Code):

  def __init__(self, pattern, body, idx):
    self.pattern = pattern
    self.idx = idx
    code = '{name}(){{\n{body}\n}}\n'.format(
      name='docopt_node_' + str(idx),
      body=body,
    )
    super(Node, self).__init__(code)


class BranchNode(Node):

  def __init__(self, pattern, idx, node_map):
    # minify arg list by only specifying node idx
    child_indexes = map(lambda child: node_map[child].idx, pattern.children)
    body = '  {helper} {args}'.format(
      helper=helper_map[type(pattern)],
      args=' '.join(list(map(str, child_indexes))),
    )
    super(BranchNode, self).__init__(pattern, body, idx)


class LeafNode(Node):

  def __init__(self, pattern, idx):
    default_value = pattern.value
    if type(pattern) is Option:
      helper_name = 'docopt_switch' if type(default_value) in [bool, int] else 'docopt_value'
      needle = idx
    elif type(pattern) is Command:
      helper_name = 'docopt_command'
      needle = pattern.name
    else:
      helper_name = 'docopt_value'
      needle = 'a'
    self.variable_name = bash_variable_name(pattern.name)

    args = [self.variable_name, bash_ifs_value(needle)]
    if type(default_value) in [list, int]:
      args.append(bash_ifs_value(True))
    elif helper_name == 'docopt_command' and args[0] == args[1]:
      args = [args[0]]
    body = '  {helper} {args}'.format(
      helper=helper_name,
      args=' '.join(args),
    )

    if type(default_value) is list:
      default_tpl = (
        '[[ -z ${{{docopt_name}+x}} ]] && eval "${{docopt_prefix}}"\'{name}={default}\' '
        '|| eval "${{docopt_prefix}}"\'{name}=("${{{docopt_name}[@]}}")\''
      )
    else:
      default_tpl = 'eval "${{docopt_prefix}}"\'{name}=${{{docopt_name}:-{default}}}\''
    self.default_assignment = default_tpl.format(
      name=self.variable_name,
      docopt_name='docopt_var_' + self.variable_name,
      default=bash_variable_value(default_value)
    )
    super(LeafNode, self).__init__(pattern, body, idx)
