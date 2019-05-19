from ... import doc
from .command import Command
from .either import Either
from .node import BranchNode
from .node import LeafNode
from .oneormore import OneOrMore
from .optional import Optional
from .required import Required
from .switch import Switch
from .value import Value

helper_map = {
  doc.Required: Required,
  doc.Optional: Optional,
  doc.OptionsShortcut: Optional,
  doc.OneOrMore: OneOrMore,
  doc.Either: Either,
}
