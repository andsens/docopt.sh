from .bash import Code, bash_variable_name, bash_variable_value, bash_ifs_value
from shlex import quote
import docopt_parser as P
from collections import OrderedDict

helper_map = {
  P.Sequence: 'sequence',
  P.Optional: 'optional',
  P.Repeatable: 'repeatable',
  P.Choice: 'choice',
}
helper_list = list(helper_map.values()) + [
  'switch',
  'value',
]


def parse_doc(doc):
  root = P.parse(doc)
  usage_match = root.mark.to_bytecount(doc)
  P.merge_identical_leaves(root, ignore_option_args=True)

  node_map = OrderedDict([])

  def get_leaves(memo, pattern):
    if isinstance(pattern, P.Leaf):
      memo.append(pattern)
    return memo

  param_sort_order = [P.Option, P.Argument, P.Command, P.ArgumentSeparator]
  unique_params = list(OrderedDict.fromkeys(root.reduce(get_leaves, [])))
  sorted_params = sorted(unique_params, key=lambda p: param_sort_order.index(type(p)))
  for idx, param in enumerate(sorted_params):
    node_map[param] = LeafNode(param, idx)

  idx = len(node_map)

  def create_groups(pattern):
    nonlocal idx
    if isinstance(pattern, P.Group):
      node_map[pattern] = BranchNode(pattern, idx, node_map)
      idx += 1
  root.walk(create_groups)

  return usage_match, node_map.values()


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
    child_indices = map(lambda child: node_map[child].idx, pattern.items)
    self.helper_name = helper_map[type(pattern)]
    body = '  {helper} {args}'.format(
      helper=self.helper_name,
      args=' '.join(list(map(str, child_indices))),
    )
    super(BranchNode, self).__init__(pattern, body, idx)


class LeafNode(Node):

  def __init__(self, pattern, idx):
    self.variable_name = bash_variable_name(
      pattern.definition.ident if isinstance(pattern, P.Option) else pattern.ident
    )
    args = [self.variable_name]
    if type(pattern) is P.Argument:
      self.helper_name = 'value'
      args.append(bash_ifs_value('a'))
    else:
      self.helper_name = 'switch' if type(pattern.default) in [bool, int] else 'value'
      args.append(bash_ifs_value(idx if type(pattern) is P.Option else f'a:{pattern.ident}'))
    if type(pattern.default) in [list, int]:
      args.append(bash_ifs_value(True))
    body = '  {helper} {args}'.format(
      helper=self.helper_name,
      args=' '.join(args),
    )

    if type(pattern.default) is list:
      assignment1 = '{name}=("${{{docopt_name}[@]}}")'.format(
        name=self.variable_name,
        docopt_name='var_' + self.variable_name
      )
      assignment2 = '{name}={default}'.format(
        name=self.variable_name,
        default=bash_variable_value(pattern.default)
      )
      self.default_assignment = (
        'if declare -p {docopt_name} >/dev/null 2>&1; then\n'
        '  eval "$p"{assignment1}\n'
        'else\n'
        '  eval "$p"{assignment2}\n'
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
        default=bash_variable_value(pattern.default)
      )
      self.default_assignment = (
        'eval "$p"{assignment}'
      ).format(
        assignment=quote(assignment)
      )
    super(LeafNode, self).__init__(pattern, body, idx)
