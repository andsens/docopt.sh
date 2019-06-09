import os.path
import re
import hashlib
import logging
import shlex
from collections import OrderedDict
from . import __version__, DocoptError
from .doc_ast import DocAst, Option
from .bash import Code, HelperTemplate, Helper, indent, bash_variable_value, bash_ifs_value, minify

log = logging.getLogger(__name__)


class Parser(object):

  def __init__(self, parser_parameters):
    self.parameters = parser_parameters
    self.library = Library()

  def patched_script(self):
    return self.script.insert_parser(str(self), self.parameters.refresh_command)

  def generate(self, script):
    generated = self.generate_main(script)
    if not self.parameters.library_path:
      generated = generated + self.generate_library()
    if self.parameters.minify:
      return generated.minify(self.parameters.max_line_length)
    else:
      return str(generated)

  def generate_main(self, script):
    if self.parameters.library_path:
      library_source = 'source %s \'%s\'' % (self.parameters.library_path, __version__)
    else:
      library_source = ''

    doc_value_start, doc_value_end = script.doc.stripped_value_boundaries
    stripped_doc = '${{DOC:{start}:{length}}}'.format(
      start=doc_value_start,
      length=doc_value_end - doc_value_start,
    )

    doc_ast = DocAst(script.doc.value, self.parameters.name_prefix)
    usage_start, usage_end = doc_ast.usage_match
    usage_doc = '${{DOC:{start}:{length}}}'.format(
      start=str(doc_value_start + usage_start),
      length=str(usage_end - usage_start),
    )

    option_nodes = [o for o in doc_ast.leaf_nodes if o.type is Option]
    defaults = []
    for node in doc_ast.leaf_nodes:
      if type(node.default_value) is list:
        tpl = "[[ -z ${{{docopt_name}+x}} ]] && {name}={default} || {name}=(\"${{{docopt_name}[@]}}\")"
      else:
        tpl = "{name}=${{{docopt_name}:-{default}}}"
      defaults.append(tpl.format(
        name=node.variable_name,
        docopt_name='docopt_var_' + node.variable_name,
        default=bash_variable_value(node.default_value)
      ))
    replacements = {
      '"LIBRARY SOURCE"': library_source,
      '"DOC VALUE"': stripped_doc,
      '"DOC USAGE"': usage_doc,
      '"DOC DIGEST"': hashlib.sha256(script.doc.value.encode('utf-8')).hexdigest()[0:5],
      '"SHORTS"': ' '.join([bash_ifs_value(o.pattern.short) for o in option_nodes]),
      '"LONGS"': ' '.join([bash_ifs_value(o.pattern.long) for o in option_nodes]),
      '"ARGCOUNT"': ' '.join([bash_ifs_value(o.pattern.argcount) for o in option_nodes]),
      '"PARAM NAMES"': ' '.join([node.variable_name for node in doc_ast.leaf_nodes]),
      '  "NODES"': indent('\n'.join(map(str, list(doc_ast.nodes)))),
      '  "DEFAULTS"': indent('\n'.join(defaults)),
      '"MAX NODE IDX"': str(max([n.idx for n in doc_ast.nodes if n is not doc_ast.root_node])),
    }
    return self.library.main.render(replacements)

  def generate_library(self, check_version=False):
    functions = OrderedDict([])
    replacements = {
      'lib_version_check': {
        '"VERSION"': __version__,
      }
    }
    for name, tpl in self.library.functions.items():
      functions[name] = tpl.render(replacements.get(name, {}))
    if check_version:
      functions['lib_version_check'] = Code(functions['lib_version_check'].body)
    else:
      del functions['lib_version_check']
    return Code(functions)


class Library(object):

  def __init__(self):
    function_re = re.compile((
        r'^(?P<name>[a-z_][a-z0-9_]*)\(\)\s*\{'
        r'\n+'
        r'(?P<body>.*?)'
        r'\n+\}$'
      ), re.MULTILINE | re.IGNORECASE | re.DOTALL)
    self.functions = OrderedDict([])
    with open(os.path.join(os.path.dirname(__file__), 'docopt.sh'), 'r') as handle:
      for match in function_re.finditer(handle.read()):
        name = match.group('name')
        body = match.group('body')
        if name == 'docopt':
          self.main = HelperTemplate(name, body)
        else:
          self.functions[name] = HelperTemplate(name, body)


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
    params['--prefix'] = ParserParameter('--prefix', invocation_params, script_params, default='')
    params['--line-length'] = ParserParameter('--line-length', invocation_params, script_params, default='80')
    params['--library'] = ParserParameter('--library', invocation_params, script_params, default=None)

    if params['--prefix'].changed:
      log.warning(
        'The parameter variable prefix is changing from `%s` to `%s`, '
        'make sure to check the variable names used in your script.',
        params['--prefix'].script_value, params['--prefix'].invocation_value
      )
    merged_from_script = list(filter(lambda p: p.merged_from_script, params.values()))
    if merged_from_script:
      log.info(
        'Adding `%s` from parser generation parameters that were detected in the script. '
        'Use --no-auto-params to disable this behavior.',
        ' '.join(map(str, merged_from_script))
      )

    self.name_prefix = params['--prefix'].value
    self.max_line_length = int(params['--line-length'].value)
    self.library_path = params['--library'].value
    self.minify = self.max_line_length > 0
    self.shorten_names = self.minify and self.library_path is not None

    command = ['docopt.sh']
    command_short = ['docopt.sh']
    if params['--prefix'].defined:
      command.append(str(params['--prefix']))
    if params['--line-length'].defined:
      command.append(str(params['--line-length']))
    if params['--library'].defined:
      command.append(str(params['--library']))
    if script is not None and script.path:
      command.append(os.path.basename(script.path))
      command_short.append(os.path.basename(script.path))
    else:
      command.append('<FILE')
      command_short.append('<FILE')
    self.refresh_command = ' '.join(command)
    self.refresh_command_short = ' '.join(command_short)
