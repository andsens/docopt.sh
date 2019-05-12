import hashlib
from .. import Function, bash_ifs_value
from ...doc import Option


class Main(Function):
  def __init__(self, settings, leaf_nodes):
    super(Main, self).__init__(settings, 'docopt')
    self.leaf_nodes = leaf_nodes

  @property
  def body(self):
    body = ''
    if self.settings.add_doc_check:
      body += '''
local current_doc_hash
local digest="{digest}"
current_doc_hash=$(printf "%s" "${docname}" | shasum -a 256 | cut -f 1 -d " ")
if [[ $current_doc_hash != "$digest" ]]; then
  printf "The current usage doc (%s) does not match what the parser was generated with (%s)\\n" \\
    "$current_doc_hash" "$digest" >&2
  exit 70
fi
'''.format(
        docname=self.settings.script.doc.name,
        digest=hashlib.sha256(self.settings.script.doc.value.encode('utf-8')).hexdigest()
      )
    # variables setup
    option_nodes = [o for o in self.leaf_nodes if o.type is Option]
    body += '''
argv=("$@")
options_short=({options_short})
options_long=({options_long})
options_argcount=({options_argcount})
param_names=({param_names})
parsed_params=()
parsed_values=()
left=()
test_match=false
local var
for var in "${{param_names[@]}}"; do
  unset "$var"
done
'''.format(
      options_short=' '.join([bash_ifs_value(o.pattern.short) for o in option_nodes]),
      options_long=' '.join([bash_ifs_value(o.pattern.long) for o in option_nodes]),
      options_argcount=' '.join([bash_ifs_value(o.pattern.argcount) for o in option_nodes]),
      param_names=' '.join([node.variable_name for node in self.leaf_nodes]),
    )
    # parse argv
    body += '''
local arg
while [[ ${#argv[@]} -gt 0 ]]; do
  if [[ ${argv[0]} = "--" ]]; then
    for arg in "${argv[@]}"; do
      parsed_params+=('a')
      parsed_values+=("$arg")
    done
    break
  elif [[ ${argv[0]} = --* ]]; then
    parse_long
  elif [[ ${argv[0]} = -* && ${argv[0]} != "-" ]]; then
    parse_shorts
  else
'''
    if self.settings.options_first:
      body += '''
    for arg in "${argv[@]}"; do
      parsed_params+=('a')
      parsed_values+=("$arg")
    done
    break
'''
    else:
      body += '''
    parsed_params+=('a')
    parsed_values+=("${argv[0]}")
    argv=("${argv[@]:1}")
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
for idx in "${{parsed_params[@]}}"; do
  [[ $idx = 'a' ]] && continue
  if [[ ${{options_short[$idx]}} = "-h" || ${{options_long[$idx]}} = "--help" ]]; then
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
for idx in "${parsed_params[@]}"; do
  [[ $idx = 'a' ]] && continue
  if [[ ${options_long[$idx]} = "--version" ]]; then
    printf "%s\\n" "$version"
    exit 0
  fi
done
'''

    # setup $left
    body += '''
local i=0
while [[ $i -lt ${#parsed_params[@]} ]]; do
  left+=("$i")
  ((i++))
done
'''
    # run the parser
    body += '''
if ! root || [ ${#left[@]} -gt 0 ]; then
  error
fi
'''
    # defaults
    if len(self.leaf_nodes) > 0:
      body += '''
defaults
'''

    # teardown
    if self.settings.add_teardown:
      body += '''
unset argv options_short options_long options_argcount param_names left \\
parsed_params parsed_values test_match; unset -f either oneormore optional \\
required _command _switch _value defaults error docopt parse_long parse_shorts
'''

    body += '''
return 0
'''
    return body
