import os.path
import re
import hashlib
import logging
import shlex
from collections import OrderedDict
from . import __version__, DocoptError
from .doc_ast import DocAst, Option
from .bash import Code, indent, bash_ifs_value
from .node import LeafNode, helper_list

log = logging.getLogger(__name__)


class Parser(object):

  def __init__(self, parser_parameters):
    self.parameters = parser_parameters
    self.library = Library()
    self.shellcheck_ignores = [
      '2016',  # Ignore unexpanded variables in single quotes (used for docopt_exit generation)
    ]
    if self.parameters.library_path:
      self.shellcheck_ignores.extend([
        '1090'   # Ignore non-constant library sourcing
        '1091',  # Ignore library sourcing
        '2034',  # Ignore unused vars (they refer to things in the library)
      ])
    if not self.parameters.library_path and self.parameters.minify:
      # Ignore else .. if issue in parse_long,
      # see https://github.com/koalaman/shellcheck/issues/1584 for more details
      self.shellcheck_ignores.append(
        '1075',
      )

  def generate(self, script):
    stripped_doc = '${{DOC:{start}:{length}}}'.format(
      start=script.doc.trimmed_value_start,
      length=len(script.doc.trimmed_value),
    )

    doc_ast = DocAst(script.doc.trimmed_value)
    usage_start, usage_end = doc_ast.usage_match
    usage_doc = '${{DOC:{start}:{length}}}'.format(
      start=str(script.doc.trimmed_value_start + usage_start),
      length=str(usage_end - usage_start),
    )

    if self.parameters.library_path:
      library = indent('''source {path} '{version}' || {{
  ret=$?
  printf -- "exit %d\\n" "$ret"
  exit "$ret"
}}'''.format(path=self.parameters.library_path, version=__version__), level=1)
    else:
      helpers_needed = set([n.helper_name for n in doc_ast.nodes])
      exclude = set(['docopt', 'lib_version_check'] + helper_list) - helpers_needed
      library = indent(str(self.library.generate_code(exclude=exclude)), level=1)

    leaf_nodes = [n for n in doc_ast.nodes if type(n) is LeafNode]
    option_nodes = [node for node in leaf_nodes if type(node.pattern) is Option]

    replacements = {
      '  "LIBRARY"': library,
      '"DOC VALUE"': stripped_doc,
      '"DOC USAGE"': usage_doc,
      '"DOC DIGEST"': hashlib.sha256(script.doc.untrimmed_value.encode('utf-8')).hexdigest()[0:5],
      '"SHORTS"': ' '.join([bash_ifs_value(o.pattern.short) for o in option_nodes]),
      '"LONGS"': ' '.join([bash_ifs_value(o.pattern.long) for o in option_nodes]),
      '"ARGCOUNTS"': ' '.join([bash_ifs_value(o.pattern.argcount) for o in option_nodes]),
      '  "NODES"': indent('\n'.join(map(str, list(doc_ast.nodes))), level=1),
      '  "OUTPUT VARNAMES ASSIGNMENTS"': indent('\n'.join([node.default_assignment for node in leaf_nodes]), level=1),
      '"INTERNAL VARNAMES"': ' \\\n    '.join(['var_%s' % node.variable_name for node in leaf_nodes]),
      '"OUTPUT VARNAMES"': ' \\\n    '.join(['"${prefix}%s"' % node.variable_name for node in leaf_nodes]),
      '  "EARLY RETURN"\n': '' if leaf_nodes else '  return 0\n',
      '"ROOT NODE IDX"': doc_ast.root_node.idx,
    }
    main = self.library.functions['docopt'].replace_literal(replacements)
    if self.parameters.minify:
      main = main.minify(self.parameters.max_line_length)
    return str(main)


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
