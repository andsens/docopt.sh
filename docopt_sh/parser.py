from .doc_parser import parse_doc, Option, Argument, Command
from .functions import helpers
from .functions import tree
from .bash_helper import minimize


class ParserSettings(object):

  def __init__(self, script, docopt_params):
    self.script = script
    self.docopt_params = docopt_params

  @property
  def name_prefix(self):
    return self.docopt_params['--prefix']

  @property
  def add_doc_check(self):
    return not self.docopt_params['--no-doc-check']

  @property
  def options_first(self):
    return self.docopt_params['--options-first']

  @property
  def add_help(self):
    return not self.docopt_params['--no-help']

  @property
  def add_version(self):
    if self.docopt_params['--no-version']:
      return False
    return self.script.version.present

  @property
  def add_teardown(self):
    return not self.docopt_params['--no-teardown']

  @property
  def minimize(self):
    return not self.docopt_params['--no-minimize']

  @property
  def max_line_length(self):
    return int(self.docopt_params['--line-length'])

  @property
  def refresh_command(self):
    command = 'docopt.sh'
    if self.docopt_params['--debug']:
      command += ' --debug'
    if self.docopt_params['--prefix'] != '':
      command += ' --prefix=' + self.docopt_params['--prefix']
    if self.docopt_params['SCRIPT'] is not None:
      command += ' ' + self.docopt_params['SCRIPT']
    return command


class Parser(object):

  def __init__(self, script, params):
    self.script = script
    self.settings = ParserSettings(script, params)
    self.pattern = parse_doc(script.doc.value)

  @property
  def patched_script(self):
    return self.script.insert_parser(str(self), self.settings.refresh_command)

  def __str__(self):
    sort_order = [Option, Argument, Command]
    sorted_params = sorted(
      set(self.pattern.flat(*sort_order)),
      key=lambda p: '%d %s' % (sort_order.index(type(p)), p.name)
    )
    for i, p in enumerate(sorted_params):
      p.index = i

    root_fn, node_functions, _ = self.pattern.get_node_functions(self.settings)
    all_functions = node_functions + [
      tree.Command(self.settings),
      tree.Either(self.settings),
      tree.OneOrMore(self.settings),
      tree.Optional(self.settings),
      tree.Required(self.settings),
      tree.Switch(self.settings),
      tree.Value(self.settings),
      helpers.ParseShorts(self.settings),
      helpers.ParseLong(self.settings),
      helpers.ParseArgv(self.settings),
      helpers.Help(self.settings),
      helpers.Error(self.settings),
      helpers.Extras(self.settings),
      helpers.Setup(self.settings, sorted_params=sorted_params),
      helpers.Teardown(self.settings),
      helpers.Check(self.settings),
      helpers.Defaults(self.settings, sorted_params=sorted_params),
      helpers.Main(self.settings, root_fn=root_fn),
    ]
    rendered_functions = [str(function) for function in all_functions if function.include()]
    parser_str = '\n'.join(rendered_functions)
    if self.settings.minimize:
      parser_str = minimize(parser_str, self.settings.max_line_length)
    return parser_str + '\n'
