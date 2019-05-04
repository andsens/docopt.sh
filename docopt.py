#!/usr/bin/env python3
import sys
import re
from shlex import quote


__all__ = ['docopt']
__version__ = '0.6.2'


class DocoptLanguageError(Exception):

    """Error in construction of usage-message by developer."""


class DocoptExit(SystemExit):

    """Exit in case user invoked program with incorrect arguments."""

    usage = ''

    def __init__(self, message=''):
        SystemExit.__init__(self, (message + '\n' + self.usage).strip())


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

    def flat(self, *types):
        return [self] if not types or type(self) in types else []

#   leaf() {
    def match(self, left, collected=None):
#       local left=(${p_left[@]})
#       if [[ $p_collected == false ]]; then
#           local collected=()
#       else
#           local collected=(${p_collected[@]})
#       fi
        collected = [] if collected is None else collected
#       $1
        pos, match = self.single_match(left)
#       pos=$r_pos
#       match=$r_match
#       if [[ $match == false ]]; then
        if match is None:
#           r_match=false
#           r_left=(${left[@]})
#           r_collected=(${collected[@]})
#           return
            return False, left, collected
#       left_=(${left[@]:0:$pos})
#       left_+=(${left[@]:((pos+1))})
        left_ = left[:pos] + left[pos + 1:]
#       for a in "${collected[@]}"; do
#           if [[ ??? == $2 ]]; then
#               same_name=???
#               break
#           fi
#       done
        same_name = [a for a in collected if a.name == self.name]
#       if ???
        if type(self.value) in (int, list):
#       if ???
            if type(self.value) is int:
#               increment=1
                increment = 1
#           else
            else:
#               ???
                increment = ([match.value] if type(match.value) is str
                             else match.value)
#           if [[ -z $same_name ]]; then
            if not same_name:
#               ??? = increment
                match.value = increment
#               r_match=true
#               r_left=(${left_[@]})
#               r_collected=(${r_collected[@]})
#               r_collected+=(match???)
#               return
                return True, left_, collected + [match]
#           fi
#           same_name???=((same_name??? + increment))
            same_name[0].value += increment
#           r_match=true
#           r_left=(${left_[@]})
#           r_collected=(${r_collected[@]})
#           r_collected[???]=same_name
#           return
            return True, left_, collected
#       fi
#       r_match=true
#       r_left=(${left_[@]})
#       r_collected=(${r_collected[@]})
#       r_collected+=(match???)
#       return
        return True, left_, collected + [match]
#   }

class BranchPattern(Pattern):

    """Branch/inner node of a pattern tree."""

    def __init__(self, *children):
        self.children = list(children)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(repr(a) for a in self.children))

    def flat(self, *types):
        if type(self) in types:
            return [self]
        return sum([child.flat(*types) for child in self.children], [])

    def get_node_functions(self, counters={}, prefix=''):
        counters[self.function_prefix] = counters.get(self.function_prefix, 0) + 1
        fn_name = '%s_%d' % (self.function_prefix, counters[self.function_prefix])
        functions = []
        function_names = []
        helpers = set()
        for child in self.children:
            if isinstance(child, BranchPattern):
                c_fn_name, c_fns, c_helpers, counters = child.get_node_functions(counters, prefix+'  ')
                functions.extend(c_fns)
                helpers.update(c_helpers)
                helpers.add(child.helper_name)
            else:
                counters[child.function_prefix] = counters.get(child.function_prefix, 0) + 1
                c_fn_name = '%s_%d' % (child.function_prefix, counters[child.function_prefix])
                c_helper, c_args = child.get_helper_invocation()
                c_fn = '%s%s(){ printf "%s\\n"; %s %s;}' % (prefix+'  ', c_fn_name, c_fn_name, c_helper, ' '.join(bash_value(arg) for arg in c_args))
                functions.append(c_fn)
                helpers.add(c_helper)
            function_names.append(c_fn_name)
        functions.insert(0, '%s%s(){ printf "%s\\n"; %s %s;}' % (prefix, fn_name, fn_name, self.helper_name, ' '.join(function_names)))
        return fn_name, functions, helpers, counters


class Argument(LeafPattern):

    function_prefix = 'arg'

#   argument()
    def single_match(self, left):
#       local name=$1
#       local left=(${p_left[@]})
#       pos=0
#       for l in "${left[@]}"; do
        for n, pattern in enumerate(left):
#           ???
            if type(pattern) is Argument:
#                   r_pos=$pos
#                   r_name=$?????
#                   r_res=$?????
#                   return
                return n, Argument(self.name, pattern.value)
#           ((pos++))
#           fi
#       done
#       r_pos=false
#       r_res=false
#       return
        return None, None
#   }

    @classmethod
    def parse(class_, source):
        name = re.findall('(<\S*?>)', source)[0]
        value = re.findall('\[default: (.*)\]', source, flags=re.I)
        return class_(name, value[0] if value else None)

    def get_helper_invocation(self):
        if type(self.value) is list:
            return '_arguments', [self.name]
        elif self.value is bool:
            return '_argument', [self.name]
        elif self.value is None:
            return '_argument', [self.name]
        else:
            return '_argument', [self.name]


class Command(Argument):

    function_prefix = 'cmd'

    def __init__(self, name, value=False):
        self.name, self.value = name, value

#   command() {
    def single_match(self, left):
#       local left=(${p_left[@]})
#       pos=0
#       for l in "${left[@]}"; do
        for n, pattern in enumerate(left):
#           ???
            if type(pattern) is Argument:
#               if [[ ??? == $1 ]]; then
                if pattern.value == self.name:
#                   r_pos=$pos
#                   r_res=$?????
#                   return
                    return n, Command(self.name, True)
#               else
                else:
#                   break
                    break
#          fi
#       done
#       r_pos=false
#       r_res=false
#       return
        return None, None
#   }

    def get_helper_invocation(self):
        if type(self.value) is int:
            return '_commands', [self.name, bash_name(self.name)]
        else:
            return '_command', [self.name, bash_name(self.name)]

class Option(LeafPattern):

    function_prefix = 'opt'

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

#   option() {
    def single_match(self, left):
#       local left=(${p_left[@]})
#       pos=0
#       for l in "${left[@]}"; do
        for n, pattern in enumerate(left):
#           if [[ $1 == $l ]]; then
            if self.name == pattern.name:
#               r_pos=$pos
#               r_res=$?????
#               return
                return n, pattern
#           fi
#       done
#       r_pos=false
#       r_res=false
#       return
        return None, None
#   }

    @property
    def name(self):
        return self.long or self.short

    def __repr__(self):
        return 'Option(%r, %r, %r, %r)' % (self.short, self.long,
                                           self.argcount, self.value)

    def get_helper_invocation(self):
        if type(self.value) is bool:
            return '_switch', [self.index, bash_name(self.name)]
        elif type(self.value) is int:
            return '_switches', [self.index, bash_name(self.name)]
        elif type(self.value) is list:
            return '_options', [self.index, bash_name(self.name)]
        elif self.value is None:
            return '_options', [self.index, bash_name(self.name)]
        else:
            return '_option', [self.index, bash_name(self.name)]


class Required(BranchPattern):

    function_prefix = 'req'
    helper_name = 'required'

#   required() {
    def match(self, left, collected=None):
#       local left=(${p_left[@]})
#       if [[ $p_collected == false ]]; then
#           local collected=()
#       else
#           local collected=(${p_collected[@]})
#       fi
        collected = [] if collected is None else collected
#       local l=(${left[@]})
        l = left
#       local c=(${collected[@]})
        c = collected
#       local matched=true
#       for pattern in "${@[@]}"; do
        for pattern in self.children:
#           p_left=(${l[@]})
#           p_collected=(${c[@]})
#           $pattern
            matched, l, c = pattern.match(l, c)
#           matched=$r_matched
#           l=(${r_left[@]})
#           c=(${r_collected[@]})
#           if ! $r_matched; then
            if not matched:
#               r_matched=false
#               r_left=(${left[@]})
#               r_collected=(${collected[@]})
#               return
                return False, left, collected
#           fi
#       done
#       r_matched=true
#       r_left=(${l[@]})
#       r_collected=(${c[@]})
#       return
        return True, l, c
#   }

class Optional(BranchPattern):

    function_prefix = 'optional'
    helper_name = 'optional'

#   optional() {
    def match(self, left, collected=None):
#       local left=(${p_left[@]})
#       if [[ $p_collected == false ]]; then
#           local collected=()
#       else
#           local collected=(${p_collected[@]})
#       fi
        collected = [] if collected is None else collected
#       for pattern in "${@[@]}"; do
        for pattern in self.children:
#           p_left=(${left[@]})
#           p_collected=(${collected[@]})
#           $pattern
            m, left, collected = pattern.match(left, collected)
#           left=(${r_left[@]})
#           collected=(${r_collected[@]})
#       done
#       r_matched=true
#       r_left=(${left[@]})
#       r_collected=(${collected[@]})
#       return
        return True, left, collected
#   }

class OptionsShortcut(Optional):

    """Marker/placeholder for [options] shortcut."""


class OneOrMore(BranchPattern):

    function_prefix = 'oneormore'
    helper_name = 'oneormore'

#   oneormore() {
    def match(self, left, collected=None):
#       assert len(self.children) == 1
        assert len(self.children) == 1
#       if [[ $p_collected == false ]]; then
#           local collected=()
#       else
#           local collected=(${p_collected[@]})
#       fi
        collected = [] if collected is None else collected
#       local l=(${p_left[@]})
        l = left
#       local c=(${collected[@]})
        c = collected
#       local l_=false
        l_ = None
#       local matched=true
        matched = True
#       local times=0
        times = 0
#       while $matched; do
        while matched:
#           p_left=(${l[@]})
#           p_collected=(${c[@]})
#           $1
            # could it be that something didn't match but changed l or c?
            matched, l, c = self.children[0].match(l, c)
#           matched=$r_matched
#           l=(${r_left[@]})
#           c=(${r_collected[@]})
#           $matched && times=((times++))
            times += 1 if matched else 0
#           if [[ ${_l[@]} == ${l[@]} ]]; then
            if l_ == l:
#               break
                break
#           fi
#           _l=${l[@]}
            l_ = l
#       done
#       if [[ $times -ge 1 ]]; then
        if times >= 1:
#           r_matched=true
#           r_left=${l[@]}
#           r_collected=${c[@]}
#           return
            return True, l, c
#       fi
#       r_matched=false
#       r_left=${left[@]}
#       r_collected=${collected[@]}
#       return
        return False, left, collected
#   }

class Either(BranchPattern):

    function_prefix = 'either'
    helper_name = 'either'

#   either() {
    def match(self, left, collected=None):
#       local left=(${p_left[@]})
#       if [[ $p_collected == false ]]; then
#           local collected=()
#       else
#           local collected=(${p_collected[@]})
#       fi
        collected = [] if collected is None else collected
#       local outcomes=()
        outcomes = []
#       local min_m
#       local min_l
#       local min_c
#       for pattern in "${@[@]}"; do
        for pattern in self.children:
#           p_left=(${l[@]})
#           p_collected=(${c[@]})
#           $pattern
            matched, _, _ = outcome = pattern.match(left, collected)
#           if [[ $r_matched && -z $min_left || ${#r_left[@]} -lt ${#min_left[@]} ]]; then
            if matched:
#               min_matched=r_matched
#               min_left=(${r_left[@]})
#               min_collected=(${r_collected[@]})
                outcomes.append(outcome)
#           fi
#       done
#       if [[ -n $min_left ]]; then
        if outcomes:
#           r_matched=min_matched
#           r_left=(${min_left[@]})
#           r_collected=(${min_collected[@]})
#           return
            return min(outcomes, key=lambda outcome: len(outcome[1]))
#       fi
#       r_matched=false
#       r_left=(${left[@]})
#       r_collected=(${collected[@]})
#       return
        return False, left, collected
#   }


class Tokens(list):

    def __init__(self, source, error=DocoptExit):
        self += source.split() if hasattr(source, 'split') else source
        self.error = error

    @staticmethod
    def from_pattern(source):
        source = re.sub(r'([\[\]\(\)\|]|\.\.\.)', r' \1 ', source)
        source = [s for s in re.split('\s+|(\S*<.*?>)', source) if s]
        return Tokens(source, error=DocoptLanguageError)

    def move(self):
        return self.pop(0) if len(self) else None

    def current(self):
        return self[0] if len(self) else None


# parse_long() {
def parse_long(tokens, options):
    """long ::= '--' chars [ ( ' ' | '=' ) chars ] ;"""
#   token=${argv[0]}
#   long=${token%%=*}
#   value=${token#*=}
#   argv=(${argv[@]:1})
    long, eq, value = tokens.move().partition('=')
    assert long.startswith('--')
#   [[ $token == --* ]] || assert_fail
#   if [[ $long = *=* ]]; then
#       eq='='
#   else
#       eq=''
#       value=false
#   fi
    value = None if eq == value == '' else value
#   local i=0
#   local similar=()
#   local similar_idx=false
#   for o in "${options_long[@]}"; do
#       if [[ $o == $long ]]; then
#           similar+=($long)
#           [[ $similar_idx == false ]] && similar_idx=$i
#       fi
#       ((i++))
#   done
    similar = [o for o in options if o.long == long]
#   if [[ ${#similar[@]} -eq 0 ]]; then
    if tokens.error is DocoptExit and similar == []:  # if no exact match
#       for o in "${options_long[@]}"; do
#           if [[ $o == $long* ]]; then
#               similar+=($long)
#               [[ $similar_idx == false ]] && similar_idx=$i
#           fi
#           ((i++))
#       done
        similar = [o for o in options if o.long and o.long.startswith(long)]
#   fi
#   if [[ ${#similar[@]} -gt 1 ]]; then
    if len(similar) > 1:  # might be simply specified ambiguously 2+ times?
#       die "%s is not a unique prefix: %s?" "$long" "${similar[*]}"
        raise tokens.error('%s is not a unique prefix: %s?' %
                           (long, ', '.join(o.long for o in similar)))
#   elif [[ ${#similar[@]} -lt 1 ]]; then
    elif len(similar) < 1:
#       if [[ $eq == '=' ]]; then
#           argcount=1
#       else
#           argcount=0
#       fi
        argcount = 1 if eq == '=' else 0
        o = Option(None, long, argcount)
#       options_short+=('')
#       options_long+=($long)
#       options_argcount+=($argcount)
#       options_value+=(false)
        options.append(o)
        if tokens.error is DocoptExit:
            o = Option(None, long, argcount, value if argcount else True)
#       parsed_options_short+=('')
#       parsed_options_long+=($long)
#       parsed_options_argcount+=($argcount)
#       if [[ argcount -eq 0 ]]; then
#           parsed_options_value[$long]=$value
#       else
#           parsed_options_value[$long]=true
#       fi
#       parsed_types+=('o')
#   else
    else:
        o = Option(similar[0].short, similar[0].long,
                   similar[0].argcount, similar[0].value)
#       if [[ $options_argcount -eq 0 ]]; then
        if o.argcount == 0:
#           if [[ $value != false ]]; then
            if value is not None:
#               die "%s must not have an argument" "$long"
                raise tokens.error('%s must not have an argument' % o.long)
#           fi
#       else
        else:
#           if [[ $value == false ]]; then
            if value is None:
#               if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
                if tokens.current() in [None, '--']:
#                   die "%s requires argument" "$long"
                    raise tokens.error('%s requires argument' % o.long)
#               fi
                value = tokens.move()
#               value=${argv[0]}
#               argv=(${argv[@]:1})
#           fi
#       fi
        if tokens.error is DocoptExit:
#       if [[ $value == false ]]; then
#           value=true
            o.value = value if value is not None else True
#       fi
#   fi
#   parsed_options_short+=(${options_short[$similar_idx]})
#   parsed_options_long+=(${options_long[$similar_idx]})
#   parsed_options_argcount+=(${options_argcount[$similar_idx]})
#   parsed_options_value+=($value)
#   parsed_types+=('o')
    return [o]
# }


# parse_shorts() {
def parse_shorts(tokens, options):
    """shorts ::= '-' ( chars )* [ [ ' ' ] chars ] ;"""
#   token=${argv[0]}
#   argv=(${argv[@]:1})
    token = tokens.move()
#   [[ $token == -* && $token != --* ]] || assert_fail
    assert token.startswith('-') and not token.startswith('--')
#   local left=${token#-}
    left = token.lstrip('-')
    parsed = []
#   while [[ -n $left ]]; do
    while left != '':
#       short="-${left:0:1}"
#       left="${left:1}"
        short, left = '-' + left[0], left[1:]
#       local i=0
#       local similar=()
#       local similar_idx=false
#       for o in "${options_short[@]}"; do
#           if [[ $o == $short ]]; then
#               similar+=($short)
#               [[ $similar_idx == false ]] && similar_idx=$i
#           fi
#           ((i++))
#       done
        similar = [o for o in options if o.short == short]
#       if [[ ${#similar[@]} -gt 1 ]]; then
        if len(similar) > 1:
#           die "%s is specified ambiguously %d times" "$short" "${#similar[@]}"
            raise tokens.error('%s is specified ambiguously %d times' %
                               (short, len(similar)))
#       elif [[ ${#similar[@]} -lt 1 ]]; then
        elif len(similar) < 1:
            o = Option(short, None, 0)
            options.append(o)
#           options_short+=($short)
#           options_long+=('')
#           options_argcount+=(0)
#           options_value+=(false)
            if tokens.error is DocoptExit:
#           parsed_options_short+=($short)
#           parsed_options_long+=('')
#           parsed_options_argcount+=(0)
#           parsed_options_value+=(true)
#           parsed_types+=('o')
                o = Option(short, None, 0, True)
#       else
        else:  # why copying is necessary here?
            o = Option(short, similar[0].long,
                       similar[0].argcount, similar[0].value)
#           value=false
            value = None
#           if [[ ${options_argcount[$similar_idx]} -neq 0 ]]; then
            if o.argcount != 0:
#               if [[ $left == '' ]]; then
                if left == '':
#                   if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
                    if tokens.current() in [None, '--']:
#                       die "%s requires argument" "$short"
                        raise tokens.error('%s requires argument' % short)
#                   fi
#                   value=${argv[0]}
#                   argv=(${argv[@]:1})
                    value = tokens.move()
#               else
                else:
#                   value=$left
                    value = left
#                   left=''
                    left = ''
#               fi
#           fi
            if tokens.error is DocoptExit:
#           if [[ $value == false ]]; then
                  o.value = value if value is not None else True
#                 option_value[$short]=true
#           fi
#       fi
#       parsed_options_short+=($short)
#       parsed_options_long+=(${options_long[$similar_idx]})
#       parsed_options_argcount+=(${options_argcount[$similar_idx]})
#       parsed_options_value+=($value)
#       parsed_types+=('o')
        parsed.append(o)
#   done
    return parsed
# }

def parse_pattern(source, options):
    tokens = Tokens.from_pattern(source)
    result = parse_expr(tokens, options)
    if tokens.current() is not None:
        raise tokens.error('unexpected ending: %r' % ' '.join(tokens))
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
            raise tokens.error("unmatched '%s'" % token)
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

# parse_argv() {
def parse_argv(tokens, options, options_first=False):
    """Parse command-line argument vector.

    If options_first:
        argv ::= [ long | shorts ]* [ argument ]* [ '--' [ argument ]* ] ;
    else:
        argv ::= [ long | shorts | argument ]* [ '--' [ argument ]* ] ;

    """
    parsed = []
#   while [[ ${#argv[@]} -gt 0 ]]; do
    while tokens.current() is not None:
#       if [[ ${argv[0]} == "--" ]]; then
        if tokens.current() == '--':
#           for arg in ${argv[@]}; do
#               parsed_arguments+=($arg)
#               parsed_types+=('a')
#           done
#           return
            return parsed + [Argument(None, v) for v in tokens]
#       elif [[ ${argv[0]} = --* ]]; then
        elif tokens.current().startswith('--'):
#           parse_long
            parsed += parse_long(tokens, options)
#       elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then
        elif tokens.current().startswith('-') and tokens.current() != '-':
#           parse_shorts
            parsed += parse_shorts(tokens, options)
#       elif $options_first; then
        elif options_first:
#           for arg in ${argv[@]}; do
#               parsed_arguments+=($arg)
#               parsed_types+=('a')
#           done
#           return
            return parsed + [Argument(None, v) for v in tokens]
#       else
        else:
#           parsed_arguments+=($arg)
#           parsed_types+=('a')
#           argv=(${argv[@]:1})
            parsed.append(Argument(None, tokens.move()))
#       fi
#   done
    return parsed
# }


def parse_defaults(doc):
    defaults = []
    for s in parse_section('options:', doc):
        # FIXME corner case "bla: options: --foo"
        _, _, s = s.partition(':')  # get rid of "options:"
        split = re.split('\n[ \t]*(-\S+?)', '\n' + s)[1:]
        split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
        options = [Option.parse(s) for s in split if s.startswith('-')]
        defaults += options
    return defaults


def parse_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]


def formal_usage(section):
    _, _, section = section.partition(':')  # drop "usage:"
    pu = section.split()
    return '( ' + ' '.join(') | (' if s == pu[0] else s for s in pu[1:]) + ' )'


def extras(help, version, options, doc):
    if help and any((o.name in ('-h', '--help')) and o.value for o in options):
        print(doc.strip("\n"))
        sys.exit()
    if version and any(o.name == '--version' and o.value for o in options):
        print(version)
        sys.exit()


class Dict(dict):
    def __repr__(self):
        return '{%s}' % ',\n '.join('%r: %r' % i for i in sorted(self.items()))


def docopt(doc, argv=None, help=True, version=None, options_first=False):
    argv = sys.argv[1:] if argv is None else argv

    usage_sections = parse_section('usage:', doc)
    if len(usage_sections) == 0:
        raise DocoptLanguageError('"usage:" (case-insensitive) not found.')
    if len(usage_sections) > 1:
        raise DocoptLanguageError('More than one "usage:" (case-insensitive).')
    DocoptExit.usage = usage_sections[0]

    options = parse_defaults(doc)
    pattern = parse_pattern(formal_usage(DocoptExit.usage), options)
    pattern_options = set(pattern.flat(Option))
    for options_shortcut in pattern.flat(OptionsShortcut):
        doc_options = parse_defaults(doc)
        options_shortcut.children = list(set(doc_options) - pattern_options)

#   parsed_options_short=()
#   parsed_options_long=()
#   parsed_options_argcount=()
#   parsed_options_value=()
#   parsed_arguments=()
#   parsed_types=()
#   argv=${@[@]}
#   parse_argv
    # argv = parse_argv(Tokens(argv), list(options), options_first)
    # extras(help, version, argv, doc)
    # matched, left, collected = pattern.fix().match(argv)
    pattern = pattern.fix()
    sort_order = [Option, Argument, Command]
    params = set(pattern.flat(*sort_order))
    sorted_params = sorted(params, key=lambda p: sort_order.index(type(p)))
    sorted_options = [o for o in sorted_params if type(o) is Option]
    for i, o in enumerate(sorted_params):
        o.index = i
    generate_ast_functions(pattern)
    print('options_short=(%s)' % ' '.join([bash_array_value(o.short) for o in sorted_options]))
    print('options_long=(%s)' % ' '.join([bash_array_value(o.long) for o in sorted_options]))
    print('options_argcount=(%s)' % ' '.join([bash_array_value(o.argcount) for o in sorted_options]))
    print('options_value=(%s)' % ' '.join([bash_array_value(o.value) for o in sorted_options]))
    print('param_names=(%s)' % ' '.join([bash_name(p.name) for p in sorted_params]))
    # print('param_defaults=(%s)' % ' '.join([bash_array_value(p.value) for p in sorted_params]))
    for p in sorted_params:
        print("{name}=${{{name}:-{default}}}".format(name=bash_name(p.name), default=bash_value(p.value)))
    # if matched and left == []:  # better error message if left?
        # err(pattern.flat())
        # err(collected)
        # [print("%s=%s" % (bash_name(a.name), a.value)) for a in (pattern.flat() + collected)]
        # return Dict((a.name, a.value) for a in (pattern.flat() + collected))
    # raise DocoptExit()

def print_ast(node, prefix=''):
    if isinstance(node, LeafPattern):
        err(prefix + type(node).__name__ + ' (%s)' % node.name)
    else:
        err(prefix + type(node).__name__)
        for child in node.children:
            print_ast(child, prefix + '  ')

helper_lib = {
    '_argument': '',
    '_arguments': '',
    '_command': '\n'.join(open('lib/command.sh').read().split('\n')[1:]),
    '_commands': '\n'.join(open('lib/commands.sh').read().split('\n')[1:]),
    '_option': '',
    '_options': '',
    '_switch': '\n'.join(open('lib/switch.sh').read().split('\n')[1:]),
    '_switches': '',
    'required': '\n'.join(open('lib/required.sh').read().split('\n')[1:]),
    'optional': 'optional(){ return;}',
    'either': '\n'.join(open('lib/either.sh').read().split('\n')[1:]),
    'oneormore': '\n'.join(open('lib/oneormore.sh').read().split('\n')[1:]),
    'parse_argv': '\n'.join(open('lib/parse_argv.sh').read().split('\n')[1:]),
    'parse_long': '\n'.join(open('lib/parse_long.sh').read().split('\n')[1:]),
    'parse_shorts': '\n'.join(open('lib/parse_shorts.sh').read().split('\n')[1:]),
    'stack': '\n'.join(open('lib/stack.sh').read().split('\n')[1:]),
    'main': '\n'.join(open('lib/main.sh').read().split('\n')[1:]),
}

def generate_ast_functions(node):
    defaults_helpers = []
    fn_name, functions, helpers, _ = node.get_node_functions()
    helpers.update(['parse_argv', 'parse_long', 'parse_shorts', 'stack', 'main'])
    print("\n".join([helper_lib[name] for name in helpers]))
    print("\n".join(functions))
    print("root(){ %s;}" % fn_name)

def bash_name(name):
    name = name.replace('<', '_')
    name = name.replace('>', '_')
    name = name.replace('-', '_')
    return name

def bash_value(value):
    if value is None:
        return ''
    if type(value) is bool:
        return 'true' if value else 'false'
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return quote(value)
    if type(value) is list:
        return '(%s)' % ' '.join(bash_value(v) for v in value)
    raise Exception('Unknown value type %s' % type(value))

def bash_array_value(value):
    if value is None or value == '':
        return "''"
    if type(value) is bool:
        return 'true' if value else 'false'
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return quote(value)
    if type(value) is list:
        raise Exception('Unable to convert list to bash array value')
    raise Exception('Unknown value type %s' % type(value))

def err(msg):
    sys.stderr.write(str(msg) + '\n')

docopt(sys.stdin.read())
