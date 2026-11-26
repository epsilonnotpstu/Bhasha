"""Compute FIRST and FOLLOW by fixed-point iteration over BNF productions.

The bundled grammar models statement structure and expression precedence.
An empty tuple represents epsilon. The functions also accept other grammars.
"""
EPSILON='ε'
GRAMMAR={
 'program':[('statements',)],
 'statements':[('statement','statements'),()],
 'statement':[('declaration',),('block',),('IF','expression','statement','else_part'),('WHILE','expression','statement'),('FOR','IDENT','=','expression','TO','expression','statement'),('FUNC','IDENT','(', 'params',')',':','type','block'),('RETURN','expression',';'),('PRINT','expression',';'),('READ','primary',';'),('BREAK',';'),('CONTINUE',';'),('expression','statement_tail')],
 'statement_tail':[('assign_op','expression',';'),(';',)],
 'assign_op':[('=',),('+=',),('-=',),('*=',),('/=',)],
 'else_part':[('ELSE','statement'),()],
 'block':[('{','statements','}')],
 'declaration':[('DECLARE','type','array_opt','IDENT','init_opt',';')],
 'type':[('INT',),('FLOAT',),('BOOL',)],
 'array_opt':[('[','expression',']'),()],
 'init_opt':[('=','expression'),()],
 'params':[('type','IDENT','params_tail'),()],
 'params_tail':[(',','type','IDENT','params_tail'),()],
 'expression':[('or_expr',)],
 'or_expr':[('and_expr','or_tail')],
 'or_tail':[('OR','and_expr','or_tail'),()],
 'and_expr':[('equality','and_tail')],
 'and_tail':[('AND','equality','and_tail'),()],
 'equality':[('ordering','equality_tail')],
 'equality_tail':[('==','ordering','equality_tail'),('!=','ordering','equality_tail'),()],
 'ordering':[('additive','ordering_tail')],
 'ordering_tail':[('<','additive','ordering_tail'),('>','additive','ordering_tail'),('<=','additive','ordering_tail'),('>=','additive','ordering_tail'),()],
 'additive':[('multiplicative','additive_tail')],
 'additive_tail':[('+','multiplicative','additive_tail'),('-','multiplicative','additive_tail'),()],
 'multiplicative':[('unary','multiplicative_tail')],
 'multiplicative_tail':[('*','unary','multiplicative_tail'),('/','unary','multiplicative_tail'),('%','unary','multiplicative_tail'),()],
 'unary':[('-','unary'),('NOT','unary'),('!','unary'),('primary',)],
 'primary':[('NUMBER',),('FLOAT_LIT',),('STRING',),('TRUE',),('FALSE',),('IDENT','identifier_tail'),('(','expression',')')],
 'identifier_tail':[('(','arguments',')'),('[','expression',']'),()],
 'arguments':[('expression','arguments_tail'),()],
 'arguments_tail':[(',','expression','arguments_tail'),()],
}

def first_sequence(sequence,first,grammar):
    result=set()
    for symbol in sequence:
        current=first[symbol] if symbol in grammar else {symbol}
        result.update(current-{EPSILON})
        if EPSILON not in current:return result
    result.add(EPSILON)
    return result

def compute(grammar,start):
    """Return FIRST and FOLLOW dictionaries for the supplied BNF grammar."""
    if start not in grammar:raise ValueError('start symbol absent from grammar')
    first={name:set() for name in grammar}
    changed=True
    while changed:
        changed=False
        for name,alternatives in grammar.items():
            for production in alternatives:
                before=len(first[name]);first[name].update(first_sequence(production,first,grammar))
                changed |= len(first[name])!=before
    follow={name:set() for name in grammar};follow[start].add('EOF')
    changed=True
    while changed:
        changed=False
        for name,alternatives in grammar.items():
            for production in alternatives:
                for i,symbol in enumerate(production):
                    if symbol not in grammar:continue
                    after=first_sequence(production[i+1:],first,grammar);before=len(follow[symbol])
                    follow[symbol].update(after-{EPSILON})
                    if EPSILON in after:follow[symbol].update(follow[name])
                    changed |= len(follow[symbol])!=before
    return first,follow

def table(grammar=GRAMMAR,start='program'):
    first,follow=compute(grammar,start)
    return '\n'.join(f"{name:15} FIRST = {{{', '.join(sorted(first[name]))}}}  FOLLOW = {{{', '.join(sorted(follow[name]))}}}" for name in grammar)

if __name__=='__main__':print(table())
