import os.path
import re
import hashlib
import logging
import shlex
from collections import OrderedDict
from . import __version__, DocoptError
import docopt_parser as P
from .bash import Code, indent, bash_variable_name, bash_variable_value, bash_ifs_value
from shlex import quote

log = logging.getLogger(__name__)


def get_leaves(memo, pattern):
  if isinstance(pattern, P.Leaf):
    memo.append(pattern)
  return memo


def get_groups(memo, pattern):
  if isinstance(pattern, P.Group):
    memo.append(pattern)
  return memo


class Parser(object):

  def __init__(self, parser_parameters):
    self.parameters = parser_parameters
    self.library = Library()

  def generate(self, script):
    root = P.parse(script.doc.trimmed_value)
    P.merge_identical_leaves(root, ignore_option_args=True)
    (usage_start, usage_end) = root.mark.to_bytecount(script.doc.trimmed_value)

    all_nodes = (
      list(OrderedDict.fromkeys(root.reduce(get_leaves, [])))
      + list(OrderedDict.fromkeys(root.reduce(get_groups, [])))
      + [root]
    )
    node_sort_order = [P.Option, P.Argument, P.Command, P.ArgumentSeparator]
    nodes = sorted(
      all_nodes,
      key=lambda p: node_sort_order.index(type(p)) if type(p) in node_sort_order else len(node_sort_order)
    )

    if self.parameters.library_path:
      library = indent(f'''source {self.parameters.library_path} '{__version__}' || {{
  ret=$?
  printf -- "exit %d\\n" "$ret"
  exit "$ret"
}}''', level=1)
    else:
      exclude = ['docopt', 'lib_version_check'] + list(set(helper_list) - set(map(helper_name, nodes)))
      library = indent(str(self.library.generate_code(exclude=exclude)), level=1)

    leaf_nodes = [node for node in nodes if isinstance(node, P.Leaf)]

    replacements = {
      '  "LIBRARY"': library,
      '"DOC VALUE"': '${{DOC:{start}:{length}}}'.format(
        start=script.doc.trimmed_value_start,
        length=len(script.doc.trimmed_value),
      ),
      '"DOC USAGE"': '${{DOC:{start}:{length}}}'.format(
        start=script.doc.trimmed_value_start + usage_start,
        length=usage_end - usage_start,
      ),
      '"DOC DIGEST"': hashlib.sha256(script.doc.untrimmed_value.encode('utf-8')).hexdigest()[0:5],
      '"OPTIONS"': ' '.join([bash_ifs_value(' '.join([
          node.short_alias or '',
          node.definition.ident if node.definition.ident.startswith('--') else '',
          '1' if node.argname else '0',
        ])) for node in leaf_nodes if type(node) is P.Option]),
      '  "NODES"': indent('\n'.join(map(str, map(lambda n: ast_cmd(n, nodes), nodes))), level=1),
      '  "OUTPUT VARNAMES ASSIGNMENTS"': indent('\n'.join([default_assignment(node) for node in leaf_nodes]), level=1),
      '"INTERNAL VARNAMES"': ' '.join([f'var_{var_name(node)}' for node in leaf_nodes]),
      '"OUTPUT VARNAMES"': ' '.join([f'"${{p}}{var_name(node)}"' for node in leaf_nodes]),
      '  "EARLY RETURN"\n': '' if leaf_nodes else '  return 0\n',
      '"ROOT NODE IDX"': len(nodes) - 1,
    }
    main = self.library.functions['docopt'].replace_literal(replacements)
    if self.parameters.minify:
      main = main.minify(self.parameters.max_line_length)

    shellcheck_ignores = [
      '2016',  # Ignore unexpanded variables in single quotes (used for docopt_exit generation)
    ]
    if self.parameters.library_path:
      shellcheck_ignores.extend([
        '1090',  # Ignore non-constant library sourcing
        '1091',  # Ignore library sourcing
        '2034',  # Ignore unused vars (they refer to things in the library)
      ])
    if not self.parameters.library_path and self.parameters.minify:
      # Ignore else .. if issue in parse_long,
      # see https://github.com/koalaman/shellcheck/issues/1584 for more details
      shellcheck_ignores.append('1075')
    if any([type(node.default) is list for node in leaf_nodes]):
      # Unlike non-array values, array values will output a "declare -p var_..."
      # to check in what way they should be set (${var:-VAL} does not work with arrays)
      # So we ignore the "referenced but not assigned" error
      shellcheck_ignores.append('2154')

    return "{shellcheck_ignores}\n{parser}".format(
      shellcheck_ignores='# shellcheck disable=%s' % ','.join(shellcheck_ignores),
      parser=main,
    )


class Library(object):

  def __init__(self):
    function_re = re.compile((
        r'^(?P<name>[a-z_][a-z0-9_]*)\(\)\s*\{'
        r'\n+'
        r'(?P<body>.*?)'
        r'\n+\}\n$'
      ), re.MULTILINE | re.IGNORECASE | re.DOTALL)
    self.functions = OrderedDict([])
    with open(os.path.join(os.path.dirname(__file__), 'docopt.sh'), 'r') as handle:
      for match in function_re.finditer(handle.read()):
        name = match.group('name')
        if name == 'lib_version_check':
          self.functions['lib_version_check'] = Code(match.group('body')).replace_literal(
            {'"LIBRARY VERSION"': __version__}
          )
        else:
          self.functions[match.group('name')] = Code(match.group(0))

  def generate_code(self, exclude=[]):
    return Code([code for name, code in self.functions.items() if name not in exclude])


class ParserParameter(object):

  def __init__(self, name, invocation_params, script_params, default):
    if script_params is None:
      script_value = None
    else:
      script_value = script_params[name]
    defined_in_invocation = invocation_params[name] is not None
    defined_in_script = script_value is not None
    auto_params = not invocation_params['--no-auto-params']

    self.name = name
    self.defined = (defined_in_invocation or defined_in_script) and auto_params
    self.invocation_value = invocation_params[name] if defined_in_invocation else default
    self.script_value = script_value if defined_in_script else default
    self.merged_from_script = not defined_in_invocation and auto_params and defined_in_script
    self.value = self.script_value if self.merged_from_script else self.invocation_value
    self.changed = script_params is not None and self.value != self.script_value

  def __str__(self):
    return '%s=%s' % (self.name, shlex.quote(self.value))


class ParserParameters(object):

  def __init__(self, invocation_params, script=None):
    if script is not None:
      script_params = script.guards.bottom.refresh_command_params
      if script_params is None:
        if script.guards.present and not invocation_params['--no-auto-params']:
          raise DocoptError(
            'Unable to auto-detect parser generation parameters. '
            'Re-run docopt.sh with `--no-auto-params`.'
          )
    else:
      script_params = None

    params = OrderedDict([])
    params['--line-length'] = ParserParameter('--line-length', invocation_params, script_params, default='80')
    params['--library'] = ParserParameter('--library', invocation_params, script_params, default=None)

    merged_from_script = list(filter(lambda p: p.merged_from_script, params.values()))
    if merged_from_script:
      log.info(
        'Adding `%s` from parser generation parameters that were detected in the script. '
        'Use --no-auto-params to disable this behavior.',
        ' '.join(map(str, merged_from_script))
      )

    self.max_line_length = int(params['--line-length'].value)
    self.library_path = params['--library'].value
    self.minify = self.max_line_length > 0

    command = ['docopt.sh']
    command_short = ['docopt.sh']
    if params['--line-length'].defined:
      command.append(str(params['--line-length']))
    if params['--library'].defined:
      command.append(str(params['--library']))
    if script is not None and script.path:
      command.append(os.path.basename(script.path))
      command_short.append(os.path.basename(script.path))
    else:
      command.append('-')
      command.append('<FILE')
      command_short.append('-')
      command_short.append('<FILE')
    self.refresh_command = ' '.join(command)
    self.refresh_command_short = ' '.join(command_short)


helper_list = ['sequence', 'choice', 'optional', 'repeatable', 'value', 'switch']


def helper_name(node):
  if isinstance(node, P.Group):
    return {
      P.Sequence: 'sequence',
      P.Choice: 'choice',
      P.Optional: 'optional',
      P.Repeatable: 'repeatable',
    }[type(node)]
  elif type(node) is P.Argument or type(node.default) not in [bool, int]:
    return 'value'
  else:
    return 'switch'


def ast_cmd(node, sorted_nodes):
  idx = sorted_nodes.index(node)
  if isinstance(node, P.Group):
    args = ' '.join([str(sorted_nodes.index(item)) for item in node.items])
  else:
    args = var_name(node)
    if type(node) is P.Argument:
      args += ' ' + bash_ifs_value('a')
    else:
      args += ' ' + bash_ifs_value(idx if type(node) is P.Option else f'a:{node.ident}')
    if type(node.default) in [list, int]:
      args += ' true'
  return Code(f'node_{idx}(){{\n  {helper_name(node)} {args}\n}}\n')


def var_name(node):
  return bash_variable_name(
    node.definition.ident if isinstance(node, P.Option) else node.ident
  )


def default_assignment(node):
  variable_name = var_name(node)
  if type(node.default) is list:
    assignment1 = '{name}=("${{{docopt_name}[@]}}")'.format(
      name=variable_name,
      docopt_name='var_' + variable_name
    )
    assignment2 = '{name}={default}'.format(
      name=variable_name,
      default=bash_variable_value(node.default)
    )
    return (
      'if declare -p {docopt_name} >/dev/null 2>&1; then\n'
      '  eval "$p"{assignment1}\n'
      'else\n'
      '  eval "$p"{assignment2}\n'
      'fi'
    ).format(
      docopt_name='var_' + variable_name,
      assignment1=quote(assignment1),
      assignment2=quote(assignment2)
    )
  else:
    assignment = '{name}=${{{docopt_name}:-{default}}}'.format(
      name=variable_name,
      docopt_name='var_' + variable_name,
      default=bash_variable_value(node.default)
    )
    return (
      'eval "$p"{assignment}'
    ).format(
      assignment=quote(assignment)
    )
