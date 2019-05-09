from .. import Function
import hashlib


class Check(Function):

  def __init__(self, doc, docname, no_doc_check):
    super(Check, self).__init__('check')
    self.doc = doc
    self.docname = docname
    self.digest = hashlib.sha256(doc.encode('utf-8')).hexdigest()
    self.no_doc_check = no_doc_check

  def include(self):
    return not self.no_doc_check

  def __str__(self):
    script = '''
local current_doc_hash
current_doc_hash=$(printf "%s" "${docname}" | shasum -a 256 | cut -f 1 -d " ")
if [[ $current_doc_hash != "{digest}" ]]; then
  printf "The current usage doc (%s) does not match what the parser was generated with ({{digest}})\\n" "$current_doc_hash" >&2
  exit 1;
fi
'''.format(docname=self.docname, digest=self.digest)
    return self.fn_wrap(script)
