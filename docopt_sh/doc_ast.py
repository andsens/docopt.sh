import re
from collections import OrderedDict
from itertools import chain
import docopt_parser as P


class DocAst(object):

  def __init__(self, doc):
    from .node import BranchNode, LeafNode
    root = P.parse(doc)
    self.usage_match = root.mark.to_bytecount(doc)
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

    self.root_node = node_map[root]
    self.nodes = node_map.values()
