from .parser import parse_doc, Option, Argument, Command
from .functions import helpers
from .functions import tree

def generate_parser(script, params):
  pattern = parse_doc(script.doc.value)
  sort_order = [Option, Argument, Command]
  sorted_params = sorted(set(pattern.flat(*sort_order)), key=lambda p: '%d %s' % (sort_order.index(type(p)), p.name))
  for i, p in enumerate(sorted_params):
    p.index = i
    p.name_prefix = params['--prefix']

  root_fn, node_functions, _ = pattern.get_node_functions()
  all_functions = node_functions + [
    tree.Command(),
    tree.Either(),
    tree.OneOrMore(),
    tree.Optional(),
    tree.Required(),
    tree.Switch(),
    tree.Value(),
    helpers.ParseShorts(),
    helpers.ParseLong(),
    helpers.ParseArgv(options_first=params['--options-first']),
    helpers.Help(docname=script.doc.name),
    helpers.Error(),
    helpers.Extras(add_help=not params['--no-help'], no_version=params['--no-version'], version_present=script.version.present),
    helpers.Setup(sorted_params=sorted_params, name_prefix=params['--prefix']),
    helpers.Teardown(no_teardown=params['--no-teardown']),
    helpers.Check(doc=script.doc.value, docname=script.doc.name, no_doc_check=params['--no-doc-check']),
    helpers.Defaults(sorted_params=sorted_params, name_prefix=params['--prefix']),
    helpers.Main(root_fn=root_fn),
  ]
  rendered_functions = [str(function) for function in all_functions if function.include()]
  return '\n'.join(rendered_functions) + '\n'
