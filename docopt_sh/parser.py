import os.path
import re
import hashlib
from collections import OrderedDict
from .doc_ast import DocAst, Option
from .bash import HelperTemplate, Helper, indent, bash_variable_value, bash_ifs_value, minify


class Parser(object):

  def __init__(self, script, params):
    self.script = script
    self.settings = ParserSettings(script, params)
    self.doc_ast = DocAst(self.settings, script.doc.value)
    self.library = Library()

  @property
  def patched_script(self):
    return self.script.insert_parser(str(self), self.settings.refresh_command)

  def generate_full_parser(self):
    all_functions = map(str, [self.generate_main()] + list(self.generate_library().values()))
    full_parser = '\n'.join(all_functions)
    if self.settings.minify:
      full_parser = minify(full_parser, self.settings.max_line_length)
    return full_parser + '\n'

  def generate_main(self):
    usage_start, usage_end = self.doc_ast.usage_match
    option_nodes = [o for o in self.doc_ast.leaf_nodes if o.type is Option]
    doc_value_start, doc_value_end = self.settings.script.doc.in_string_value_match
    doc_name = '${{{docname}:{start}:{end}}}'.format(
      docname=self.settings.script.doc.name,
      start=doc_value_start,
      end=doc_value_end,
    )
    defaults = []
    for node in self.doc_ast.leaf_nodes:
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
      '"DOC VALUE"': doc_name,
      '"DOC DIGEST"': hashlib.sha256(self.settings.script.doc.value.encode('utf-8')).hexdigest()[0:5],
      '"SHORT USAGE START"': str(usage_start),
      '"SHORT USAGE LENGTH"': str(usage_end - usage_start),
      '"SHORTS"': ' '.join([bash_ifs_value(o.pattern.short) for o in option_nodes]),
      '"LONGS"': ' '.join([bash_ifs_value(o.pattern.long) for o in option_nodes]),
      '"ARGCOUNT"': ' '.join([bash_ifs_value(o.pattern.argcount) for o in option_nodes]),
      '"PARAM NAMES"': ' '.join([node.variable_name for node in self.doc_ast.leaf_nodes]),
      '  "NODES"': indent('\n'.join(map(str, list(self.doc_ast.nodes)))),
      '  "DEFAULTS"': indent('\n'.join(defaults)),
      '"MAX NODE IDX"': str(max([n.idx for n in self.doc_ast.nodes if n is not self.doc_ast.root_node])),
    }
    return self.library.main.render(replacements)

  def generate_library(self):
    functions = OrderedDict([])
    for name, tpl in self.library.functions.items():
      functions[name] = tpl.render()
    return functions

  def __str__(self):
    return self.generate_full_parser()


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


class ParserSettings(object):

  def __init__(self, script, docopt_params):
    self.script = script
    self.docopt_params = docopt_params

  @property
  def name_prefix(self):
    return self.docopt_params['--prefix']

  @property
  def minify(self):
    return not self.docopt_params['--no-minify']

  @property
  def max_line_length(self):
    return int(self.docopt_params['--line-length'])

  @property
  def refresh_command(self):
    command = 'docopt.sh'
    if self.docopt_params['--prefix'] != '':
      command += ' --prefix=' + self.docopt_params['--prefix']
    if self.docopt_params['SCRIPT'] is not None:
      command += ' ' + os.path.basename(self.docopt_params['SCRIPT'])
    return command
