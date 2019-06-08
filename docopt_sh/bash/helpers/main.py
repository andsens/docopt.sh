import hashlib
from .. import Function, bash_ifs_value
from ...doc import Option


class Main(Function):
  def __init__(self, settings, root_node, leaf_nodes):
    super(Main, self).__init__(settings, 'docopt')
    self.root_node = root_node
    self.leaf_nodes = leaf_nodes

  @property
  def body(self):
    body = ''
    if self.settings.add_doc_check:
      body += '''
local doc_hash
local digest="{digest}"
doc_hash=$(printf "%s" "${docname}" | shasum -a 256)
if [[ ${{doc_hash:0:5}} != "$digest" ]]; then
  printf "The current usage doc (%s) does not match what the parser was generated with (%s)\\n" \\
    "$doc_hash" "$digest" >&2
  exit 70
fi
'''.format(
        docname=self.settings.script.doc.name,
        digest=hashlib.sha256(self.settings.script.doc.value.encode('utf-8')).hexdigest()[0:5]
      )
    # variables setup
    option_nodes = [o for o in self.leaf_nodes if o.type is Option]
    body += '''
docopt_argv=("$@")
docopt_shorts=({options_short})
docopt_longs=({options_long})
docopt_argcount=({options_argcount})
docopt_param_names=({param_names})
docopt_parsed_params=()
docopt_parsed_values=()
docopt_left=()
docopt_testmatch=false
local var
for var in "${{docopt_param_names[@]}}"; do
  unset "$var"
done
'''.format(
      options_short=' '.join([bash_ifs_value(o.pattern.short) for o in option_nodes]),
      options_long=' '.join([bash_ifs_value(o.pattern.long) for o in option_nodes]),
      options_argcount=' '.join([bash_ifs_value(o.pattern.argcount) for o in option_nodes]),
      param_names=' '.join([node.variable_name for node in self.leaf_nodes]),
    )
    # parse docopt_argv
    body += '''
local arg
while [[ ${#docopt_argv[@]} -gt 0 ]]; do
  if [[ ${docopt_argv[0]} = "--" ]]; then
    for arg in "${docopt_argv[@]}"; do
      docopt_parsed_params+=('a')
      docopt_parsed_values+=("$arg")
    done
    break
  elif [[ ${docopt_argv[0]} = --* ]]; then
    docopt_parse_long
  elif [[ ${docopt_argv[0]} = -* && ${docopt_argv[0]} != "-" ]]; then
    docopt_parse_shorts
  else
'''
    if self.settings.options_first:
      body += '''
    for arg in "${docopt_argv[@]}"; do
      docopt_parsed_params+=('a')
      docopt_parsed_values+=("$arg")
    done
    break
'''
    else:
      body += '''
    docopt_parsed_params+=('a')
    docopt_parsed_values+=("${docopt_argv[0]}")
    docopt_argv=("${docopt_argv[@]:1}")
'''
    body += '''
  fi
done
'''

    # extras
    if self.settings.add_help or self.settings.add_version:
      body += 'local idx'
    if self.settings.add_help:
      body += '''
for idx in "${{docopt_parsed_params[@]}}"; do
  [[ $idx = 'a' ]] && continue
  if [[ ${{docopt_shorts[$idx]}} = "-h" || ${{docopt_longs[$idx]}} = "--help" ]]; then
    printf -- "{template}" "${docname}"
    exit 0
  fi
done
'''.format(
        template='%s' if self.settings.script.doc.value.endswith('\n') else '%s\\n',
        docname=self.settings.script.doc.name,
      )
    if self.settings.add_version:
      body += '''
for idx in "${docopt_parsed_params[@]}"; do
  [[ $idx = 'a' ]] && continue
  if [[ ${docopt_longs[$idx]} = "--version" ]]; then
    printf "%s\\n" "$version"
    exit 0
  fi
done
'''

    # setup $docopt_left
    body += '''
local i=0
while [[ $i -lt ${#docopt_parsed_params[@]} ]]; do
  docopt_left+=("$i")
  ((i++))
done
'''
    # run the parser
    body += '''
if ! {root} || [ ${{#docopt_left[@]}} -gt 0 ]; then
  docopt_error
fi
'''.format(root=self.root_node.body)
    # defaults
    if len(self.leaf_nodes) > 0:
      body += '''
docopt_defaults
'''

    # teardown
    if self.settings.add_teardown:
      body += '''
unset docopt_argv docopt_shorts docopt_longs docopt_argcount docopt_param_names \\
docopt_left docopt_parsed_params docopt_parsed_values docopt_testmatch
unset -f docopt_either docopt_oneormore docopt_optional docopt_required \\
docopt_command docopt_switch docopt_value docopt_defaults \\
docopt_error docopt_parse_long docopt_parse_shorts docopt
'''

    body += '''
return 0
'''
    return body
