from parser import Option, Argument, Command
from bash_helper import bash_name, bash_value, bash_array_value
import hashlib

def generate_parser(pattern, docname, debug=False):
    sort_order = [Option, Argument, Command]
    params = set(pattern.flat(*sort_order))
    sorted_params = sorted(params, key=lambda p: sort_order.index(type(p)))
    sorted_options = [o for o in sorted_params if type(o) is Option]
    for i, o in enumerate(sorted_params):
        o.index = i

    ast_functions = generate_ast_functions(pattern, debug=debug)
    help_fn = render_template('lib/help.sh', {"{{doc}}": '$' + docname})
    parameter_details = '\n'.join([
        'options_short=(%s)' % ' '.join([bash_array_value(o.short) for o in sorted_options]),
        'options_long=(%s)' % ' '.join([bash_array_value(o.long) for o in sorted_options]),
        'options_argcount=(%s)' % ' '.join([bash_array_value(o.argcount) for o in sorted_options]),
        'param_names=(%s)' % ' '.join([bash_name(p.name) for p in sorted_params]),
    ])
    if sorted_params:
        defaults = 'defaults() {\n'
        for p in sorted_params:
            if type(p.value) is list:
                defaults += "  [[ -z ${{{name}+x}} ]] && {name}={default}\n".format(name=bash_name(p.name), default=bash_value(p.value))
            else:
                defaults += "  {name}=${{{name}:-{default}}}\n".format(name=bash_name(p.name), default=bash_value(p.value))
        defaults += '}'
    return '\n'.join([ast_functions, help_fn, parameter_details, defaults]) + '\n'

def generate_doc_check(parser, doc, docname):
    digest = hashlib.sha256(doc.encode('utf-8')).hexdigest()
    return '''current_doc_hash=$(printf "%s" "${docname}" | shasum -a 256 | cut -f 1 -d " ")
if [[ $current_doc_hash != "{digest}" ]]; then
  printf "The current usage doc (%s) does not match what the parser was generated with ({digest})\n" "$current_doc_hash" >&2
  exit 1;
fi
unset current_doc_hash
'''.format(docname=docname, digest=digest)

def generate_invocation(parser):
    return 'docopt "$@"\n'

helper_lib = {
    '_command': '\n'.join(open('lib/leaves/command.sh').read().split('\n')[1:]).strip('\n'),
    '_switch': '\n'.join(open('lib/leaves/switch.sh').read().split('\n')[1:]).strip('\n'),
    '_value': '\n'.join(open('lib/leaves/value.sh').read().split('\n')[1:]).strip('\n'),
    'required': '\n'.join(open('lib/branches/required.sh').read().split('\n')[1:]).strip('\n'),
    'optional': '\n'.join(open('lib/branches/optional.sh').read().split('\n')[1:]).strip('\n'),
    'either': '\n'.join(open('lib/branches/either.sh').read().split('\n')[1:]).strip('\n'),
    'oneormore': '\n'.join(open('lib/branches/oneormore.sh').read().split('\n')[1:]).strip('\n'),
    'parse_argv': '\n'.join(open('lib/parse_argv.sh').read().split('\n')[1:]).strip('\n'),
    'parse_long': '\n'.join(open('lib/parse_long.sh').read().split('\n')[1:]).strip('\n'),
    'parse_shorts': '\n'.join(open('lib/parse_shorts.sh').read().split('\n')[1:]).strip('\n'),
    'extras': '\n'.join(open('lib/extras.sh').read().split('\n')[1:]).strip('\n'),
    'main': '\n'.join(open('lib/main.sh').read().split('\n')[1:]).strip('\n'),
    'debug': '\n'.join(open('lib/debug.sh').read().split('\n')[1:]).strip('\n'),
}

def generate_ast_functions(node, debug=False):
    defaults_helpers = []
    fn_name, functions, helpers, _ = node.get_node_functions(debug=debug)
    helpers.update(['parse_argv', 'parse_long', 'parse_shorts', 'extras', 'main'])
    if debug:
        helpers.add('debug')
    root = "root(){ %s;}" % fn_name
    return '\n'.join([helper_lib[name] for name in helpers] + functions + [root])

def render_template(file, variables):
    with open(file, 'r') as h:
        contents = h.read()
        for name, replacement in variables.items():
            contents = contents.replace(name, replacement)
    return contents
