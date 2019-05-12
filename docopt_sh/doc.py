import re
from collections import OrderedDict
from itertools import chain


class DocAst(object):

  def __init__(self, settings, doc):
    from .bash.tree.node import BranchNode, LeafNode
    self.settings = settings
    self.doc = doc
    self.root, self.usage_match = parse_doc(doc)
    self.nodes = OrderedDict([])
    param_sort_order = [Option, Argument, Command]
    unique_params = list(OrderedDict.fromkeys(self.root.flat(*param_sort_order)))
    sorted_params = sorted(unique_params, key=lambda p: param_sort_order.index(type(p)))
    for idx, param in enumerate(sorted_params):
      self.nodes[param] = LeafNode(settings, param, idx)
    for idx, pattern in enumerate(iter(self.root)):
      if isinstance(pattern, BranchPattern):
        self.nodes[pattern] = BranchNode(settings, pattern, idx, self.nodes)
    self.nodes[self.root].name = 'root'

  @property
  def functions(self):
    return list(self.nodes.values())

  @property
  def sorted_params(self):
    params = [Option, Argument, Command]
    return [key for key in self.nodes.keys() if type(key) in params]

  @property
  def usage_section(self):
    return self.usage_match.start(0), self.usage_match.end(0)


def parse_doc(doc):
  usage_sections = parse_section('usage:', doc)
  if len(usage_sections) == 0:
    raise DocoptLanguageError('"usage:" (case-insensitive) not found.')
  if len(usage_sections) > 1:
    raise DocoptLanguageError('More than one "usage:" (case-insensitive).')
  usage, usage_match = usage_sections[0]

  options = parse_defaults(doc)
  pattern = parse_pattern(formal_usage(usage), options)
  pattern_options = set(pattern.flat(Option))
  for options_shortcut in pattern.flat(OptionsShortcut):
    doc_options = parse_defaults(doc)
    options_shortcut.children = list(set(doc_options) - pattern_options)

  return pattern.fix(), usage_match


class DocoptLanguageError(Exception):

  """Error in construction of usage-message by developer."""


class Pattern(object):

  def __eq__(self, other):
    return repr(self) == repr(other)

  def __hash__(self):
    return hash(repr(self))

  def fix(self):
    self.fix_identities()
    self.fix_repeating_arguments()
    return self

  def fix_identities(self, uniq=None):
    """Make pattern-tree tips point to same object if they are equal."""
    if not hasattr(self, 'children'):
      return self
    uniq = list(set(self.flat())) if uniq is None else uniq
    for i, child in enumerate(self.children):
      if not hasattr(child, 'children'):
        assert child in uniq
        self.children[i] = uniq[uniq.index(child)]
      else:
        child.fix_identities(uniq)

  def fix_repeating_arguments(self):
    """Fix elements that should accumulate/increment values."""
    either = [list(child.children) for child in transform(self).children]
    for case in either:
      for e in [child for child in case if case.count(child) > 1]:
        if type(e) is Argument or type(e) is Option and e.argcount:
          if e.value is None:
            e.value = []
          elif type(e.value) is not list:
            e.value = e.value.split()
        if type(e) is Command or type(e) is Option and e.argcount == 0:
          e.value = 0
    return self


def transform(pattern):
  """Expand pattern into an (almost) equivalent one, but with single Either.

  Example: ((-a | -b) (-c | -d)) => (-a -c | -a -d | -b -c | -b -d)
  Quirks: [-a] => (-a), (-a...) => (-a -a)

  """
  result = []
  groups = [[pattern]]
  while groups:
    children = groups.pop(0)
    parents = [Required, Optional, OptionsShortcut, Either, OneOrMore]
    if any(t in map(type, children) for t in parents):
      child = [c for c in children if type(c) in parents][0]
      children.remove(child)
      if type(child) is Either:
        for c in child.children:
          groups.append([c] + children)
      elif type(child) is OneOrMore:
        groups.append(child.children * 2 + children)
      else:
        groups.append(child.children + children)
    else:
      result.append(children)
  return Either(*[Required(*e) for e in result])


class LeafPattern(Pattern):

  """Leaf/terminal node of a pattern tree."""

  def __init__(self, name, value=None):
    self.name, self.value = name, value

  def __repr__(self):
    return '%s(%r, %r)' % (self.__class__.__name__, self.name, self.value)

  def __iter__(self):
    yield self

  def flat(self, *types):
    return [self] if not types or type(self) in types else []


class BranchPattern(Pattern):

  """Branch/inner node of a pattern tree."""

  def __init__(self, *children):
    self.children = list(children)

  def __repr__(self):
    return '%s(%s)' % (self.__class__.__name__, ', '.join(repr(a) for a in self.children))

  def __iter__(self):
    for child in chain(*map(iter, self.children)):
      yield child
    yield self

  def flat(self, *types):
    if type(self) in types:
      return [self]
    return sum([child.flat(*types) for child in self.children], [])


class Argument(LeafPattern):

  @classmethod
  def parse(class_, source):
    name = re.findall('(<\S*?>)', source)[0]
    value = re.findall('\[default: (.*)\]', source, flags=re.I)
    return class_(name, value[0] if value else None)


class Command(Argument):

  def __init__(self, name, value=False):
    self.name, self.value = name, value


class Option(LeafPattern):

  def __init__(self, short=None, long=None, argcount=0, value=False):
    assert argcount in (0, 1)
    self.short, self.long, self.argcount = short, long, argcount
    self.value = None if value is False and argcount else value

  @classmethod
  def parse(class_, option_description):
    short, long, argcount, value = None, None, 0, False
    options, _, description = option_description.strip().partition('  ')
    options = options.replace(',', ' ').replace('=', ' ')
    for s in options.split():
      if s.startswith('--'):
        long = s
      elif s.startswith('-'):
        short = s
      else:
        argcount = 1
    if argcount:
      matched = re.findall('\[default: (.*)\]', description, flags=re.I)
      value = matched[0] if matched else None
    return class_(short, long, argcount, value)

  @property
  def name(self):
    return self.long or self.short

  def __repr__(self):
    return 'Option(%r, %r, %r, %r)' % (self.short, self.long, self.argcount, self.value)


class Required(BranchPattern):
  pass


class Optional(BranchPattern):
  pass


class OptionsShortcut(Optional):
  """Marker/placeholder for [options] shortcut."""


class OneOrMore(BranchPattern):
  pass


class Either(BranchPattern):
  pass


class Tokens(list):

  def __init__(self, source):
    self += source.split() if hasattr(source, 'split') else source

  @staticmethod
  def from_pattern(source):
    source = re.sub(r'([\[\]\(\)\|]|\.\.\.)', r' \1 ', source)
    source = [s for s in re.split('\s+|(\S*<.*?>)', source) if s]
    return Tokens(source)

  def move(self):
    return self.pop(0) if len(self) else None

  def current(self):
    return self[0] if len(self) else None


def parse_long(tokens, options):
  """long ::= '--' chars [ ( ' ' | '=' ) chars ] ;"""
  long, eq, value = tokens.move().partition('=')
  assert long.startswith('--')
  value = None if eq == value == '' else value
  similar = [o for o in options if o.long == long]
  if len(similar) > 1:  # might be simply specified ambiguously 2+ times?
    raise DocoptLanguageError('%s is not a unique prefix: %s?' % (long, ', '.join(o.long for o in similar)))
  elif len(similar) < 1:
    argcount = 1 if eq == '=' else 0
    o = Option(None, long, argcount)
    options.append(o)
  else:
    o = Option(similar[0].short, similar[0].long, similar[0].argcount, similar[0].value)
    if o.argcount == 0:
      if value is not None:
        raise DocoptLanguageError('%s must not have an argument' % o.long)
    else:
      if value is None:
        if tokens.current() in [None, '--']:
          raise DocoptLanguageError('%s requires argument' % o.long)
        value = tokens.move()
  return [o]


def parse_shorts(tokens, options):
  """shorts ::= '-' ( chars )* [ [ ' ' ] chars ] ;"""
  token = tokens.move()
  assert token.startswith('-') and not token.startswith('--')
  left = token.lstrip('-')
  parsed = []
  while left != '':
    short, left = '-' + left[0], left[1:]
    similar = [o for o in options if o.short == short]
    if len(similar) > 1:
      raise DocoptLanguageError('%s is specified ambiguously %d times' % (short, len(similar)))
    elif len(similar) < 1:
      o = Option(short, None, 0)
      options.append(o)
    else:  # why copying is necessary here?
      o = Option(short, similar[0].long, similar[0].argcount, similar[0].value)
      value = None
      if o.argcount != 0:
        if left == '':
          if tokens.current() in [None, '--']:
            raise DocoptLanguageError('%s requires argument' % short)
          value = tokens.move()
        else:
          value = left
          left = ''
    parsed.append(o)
  return parsed


def parse_pattern(source, options):
  tokens = Tokens.from_pattern(source)
  result = parse_expr(tokens, options)
  if tokens.current() is not None:
    raise DocoptLanguageError('unexpected ending: %r' % ' '.join(tokens))
  return Required(*result)


def parse_expr(tokens, options):
  """expr ::= seq ( '|' seq )* ;"""
  seq = parse_seq(tokens, options)
  if tokens.current() != '|':
    return seq
  result = [Required(*seq)] if len(seq) > 1 else seq
  while tokens.current() == '|':
    tokens.move()
    seq = parse_seq(tokens, options)
    result += [Required(*seq)] if len(seq) > 1 else seq
  return [Either(*result)] if len(result) > 1 else result


def parse_seq(tokens, options):
  """seq ::= ( atom [ '...' ] )* ;"""
  result = []
  while tokens.current() not in [None, ']', ')', '|']:
    atom = parse_atom(tokens, options)
    if tokens.current() == '...':
      atom = [OneOrMore(*atom)]
      tokens.move()
    result += atom
  return result


def parse_atom(tokens, options):
  """atom ::= '(' expr ')' | '[' expr ']' | 'options'
       | long | shorts | argument | command ;
  """
  token = tokens.current()
  result = []
  if token in '([':
    tokens.move()
    matching, pattern = {'(': [')', Required], '[': [']', Optional]}[token]
    result = pattern(*parse_expr(tokens, options))
    if tokens.move() != matching:
      raise DocoptLanguageError("unmatched '%s'" % token)
    return [result]
  elif token == 'options':
    tokens.move()
    return [OptionsShortcut()]
  elif token.startswith('--') and token != '--':
    return parse_long(tokens, options)
  elif token.startswith('-') and token not in ('-', '--'):
    return parse_shorts(tokens, options)
  elif token.startswith('<') and token.endswith('>') or token.isupper():
    return [Argument(tokens.move())]
  else:
    return [Command(tokens.move())]


def parse_defaults(doc):
  defaults = []
  for s, _ in parse_section('options:', doc):
    # FIXME corner case "bla: options: --foo"
    _, _, s = s.partition(':')  # get rid of "options:"
    split = re.split('\n[ \t]*(-\S+?)', '\n' + s)[1:]
    split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
    options = [Option.parse(s) for s in split if s.startswith('-')]
    defaults += options
  return defaults


def parse_section(name, source):
  pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)', re.IGNORECASE | re.MULTILINE)
  return [(m.group(0).strip(), m) for m in pattern.finditer(source)]


def formal_usage(section):
  _, _, section = section.partition(':')  # drop "usage:"
  pu = section.split()
  return '( ' + ' '.join(') | (' if s == pu[0] else s for s in pu[1:]) + ' )'
