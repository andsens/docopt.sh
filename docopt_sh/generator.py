from docopt_sh.parser import Option, Argument, Command
from docopt_sh.bash_helper import bash_name, bash_value, bash_array_value
import hashlib

def generate_parser(pattern, docname, debug=False):
    sort_order = [Option, Argument, Command]
    params = set(pattern.flat(*sort_order))
    sorted_params = sorted(params, key=lambda p: sort_order.index(type(p)))
    sorted_options = [o for o in sorted_params if type(o) is Option]
    for i, o in enumerate(sorted_params):
        o.index = i

    root_fn, ast_functions = generate_ast_functions(pattern, debug=debug)
    all_functions = [
        ast_functions,
        render_template('lib/help.sh', {"{{doc}}": '$' + docname}),
        render_template('lib/setup.sh', {
            '{{options_short}}': ' '.join([bash_array_value(o.short) for o in sorted_options]),
            '{{options_long}}': ' '.join([bash_array_value(o.long) for o in sorted_options]),
            '{{options_argcount}}': ' '.join([bash_array_value(o.argcount) for o in sorted_options]),
            '{{param_names}}': ' '.join([bash_name(p.name) for p in sorted_params]),
        }),
        render_template('lib/docopt.sh', {"{{root_fn}}": root_fn}),
    ]
    if sorted_params:
        default_values = generate_default_values(sorted_params)
        all_functions.append(render_template('lib/defaults.sh', {'{{defaults}}': '\n'.join(default_values)}))
    return '\n'.join(all_functions) + '\n'

def generate_teardown():
    return render_template('lib/teardown.sh') + '\n'

def generate_doc_check(parser, doc, docname):
    digest = hashlib.sha256(doc.encode('utf-8')).hexdigest()
    docopt_check = render_template('lib/check_hash.sh', {'{{docname}}': docname, '{{digest}}': digest})
    return docopt_check + '\n' + 'docopt_check' +'\n'

helper_lib = {
    '_command': 'lib/leaves/command.sh',
    '_switch': 'lib/leaves/switch.sh',
    '_value': 'lib/leaves/value.sh',
    'required': 'lib/branches/required.sh',
    'optional': 'lib/branches/optional.sh',
    'either': 'lib/branches/either.sh',
    'oneormore': 'lib/branches/oneormore.sh',
    'parse_argv': 'lib/parse_argv.sh',
    'parse_long': 'lib/parse_long.sh',
    'parse_shorts': 'lib/parse_shorts.sh',
    'extras': 'lib/extras.sh',
    'debug': 'lib/debug.sh',
}

def generate_ast_functions(node, debug=False):
    defaults_helpers = []
    fn_name, functions, helpers, _ = node.get_node_functions(debug=debug)
    helpers.update(['parse_argv', 'parse_long', 'parse_shorts', 'extras'])
    if debug:
        helpers.add('debug')
    return fn_name, '\n'.join([render_template(helper_lib[name]) for name in helpers] + functions)

def generate_default_values(params):
    for p in params:
        if type(p.value) is list:
            yield "  [[ -z ${{{name}+x}} ]] && {name}={default}".format(name=bash_name(p.name), default=bash_value(p.value))
        else:
            yield "  {name}=${{{name}:-{default}}}".format(name=bash_name(p.name), default=bash_value(p.value))

def render_template(file, variables={}):
    with open(file, 'r') as h:
        contents = h.read()
        contents = contents.lstrip('#!/usr/bin/env bash')
        contents = contents.strip('\n')
        for name, replacement in variables.items():
            contents = contents.replace(name, replacement)
    return contents
