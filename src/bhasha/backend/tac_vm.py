"""Execute printable three-address code with per-call local frames."""
import ast
import operator
import re
from collections import ChainMap
from .vm import checked_index, format_value, parse_numeric_input

class TacRuntimeError(ValueError): pass
NAME=r'[^\s(),\[\]:=]+'

def execute(lines, max_steps=100000, input_fn=input, output_fn=None):
    labels={line[:-1]:i for i,line in enumerate(lines) if re.fullmatch(r'[A-Za-z_]\w*:',line)}
    global_env={};env=global_env;global_names=set(); output=[]; pc=0; steps=0; pending=[]; frames=[]; functions={}; ends={}; active=None
    for i,line in enumerate(lines):
        header=re.fullmatch(rf'func ({NAME})\(([^)]*)\):',line)
        if header:
            if active is not None:raise TacRuntimeError('nested functions unsupported')
            active=i;functions[header.group(1)]=(i+1,[x.strip() for x in header.group(2).split(',') if x.strip()])
        elif line=='endfunc':
            if active is None:raise TacRuntimeError('unexpected endfunc')
            ends[active]=i;active=None
    def value(text):
        text=text.strip()
        indexed=re.fullmatch(rf'({NAME})\[(.+)\]',text)
        if indexed:
            array=env[indexed.group(1)];return array[checked_index(array,value(indexed.group(2)))]
        try:return ast.literal_eval(text)
        except (ValueError,SyntaxError):
            if text in env:return env[text]
            raise TacRuntimeError(f'unknown operand: {text}')
    def expr(text):
        parts=text.split()
        if len(parts)==1:return value(parts[0])
        if len(parts)==2 and parts[0] in ('-','NOT','!','float'):
            operand=value(parts[1]);return float(operand) if parts[0]=='float' else -operand if parts[0]=='-' else not operand
        if len(parts)==3:
            a,op,b=value(parts[0]),parts[1],value(parts[2])
            if op in ('/','%') and type(a) is int and type(b) is int:
                q=abs(a)//abs(b);q=-q if (a<0)!=(b<0) else q
                return q if op=='/' else a-q*b
            funcs={'+':operator.add,'-':operator.sub,'*':operator.mul,'/':operator.truediv,'%':operator.mod,'==':operator.eq,'!=':operator.ne,'<':operator.lt,'>':operator.gt,'<=':operator.le,'>=':operator.ge,'AND':lambda x,y:x and y,'OR':lambda x,y:x or y}
            if op in funcs:return funcs[op](a,b)
        raise TacRuntimeError(f'unsupported expression: {text}')
    while pc<len(lines):
        steps+=1
        if steps>max_steps:raise TacRuntimeError('execution step limit exceeded')
        line=lines[pc];pc+=1
        if line.startswith('global '):global_names.add(line[7:]);continue
        if line.startswith('func '):
            if pc-1 not in ends:raise TacRuntimeError('function missing endfunc')
            pc=ends[pc-1]+1;continue
        if line.startswith('param '):pending.append(value(line[6:]));continue
        call=re.fullmatch(rf'({NAME}) = call ({NAME}), (\d+)',line)
        if call:
            target,name,count=call.group(1),call.group(2),int(call.group(3))
            if name not in functions:raise TacRuntimeError(f'unknown function: {name}')
            entry,params=functions[name]
            if count!=len(params) or count>len(pending):raise TacRuntimeError('incorrect function arguments')
            args=pending[-count:] if count else []
            if count:del pending[-count:]
            frames.append((pc,env,target));env=ChainMap(dict(zip(params,args)),global_env);pc=entry;continue
        if line.startswith('return '):
            if not frames:raise TacRuntimeError('return outside function')
            result=expr(line[7:]);pc,env,target=frames.pop();env[target]=result;continue
        if line=='endfunc':raise TacRuntimeError('function ended without return')
        if line.endswith(':'):continue
        if line.startswith('goto '):pc=labels[line[5:]];continue
        branch=re.fullmatch(r'ifFalse (.+) goto (\w+)',line)
        if branch:
            if not expr(branch.group(1)):pc=labels[branch.group(2)]
            continue
        if line.startswith('print '):
            raw=line[6:]
            try:v=ast.literal_eval(raw)
            except (SyntaxError,ValueError):v=expr(raw)
            rendered=format_value(v);output.append(rendered)
            if output_fn is not None:output_fn(rendered)
            continue
        if line.startswith('read '):
            name=line[5:];raw=input_fn();target=global_env if frames and name in global_names else env;target[name]=parse_numeric_input(raw,isinstance(env.get(name),float));continue
        array=re.fullmatch(rf'array (\S+) ({NAME}) (.+)',line)
        if array:
            typ,name,size_text=array.groups();size=value(size_text)
            if type(size) is not int or size<0:raise TacRuntimeError('invalid array size')
            zero=0.0 if typ in ('doshomik','দশমিক') else False if typ=='huen' else 0
            env[name]=[zero]*size;continue
        store=re.fullmatch(rf'({NAME})\[(.+)\] = (.+)',line)
        if store:
            result=expr(store.group(3));array=env[store.group(1)];array[checked_index(array,value(store.group(2)))]=result;continue
        decl=re.fullmatch(rf'decl \S+ ({NAME})',line)
        if decl:env[decl.group(1)]=0.0 if line.split()[1] in ('doshomik','দশমিক') else 0;continue
        assignment=re.fullmatch(rf'({NAME}) (\+=|-=|\*=|/=|=) (.+)',line)
        if assignment:
            name,op,rhs=assignment.groups();v=expr(rhs)
            if op!='=':v=expr(f'{name} {op[0]} {v}')
            target=global_env if frames and name in global_names else env;target[name]=v;continue
        raise TacRuntimeError(f'unsupported TAC instruction: {line}')
    return '\n'.join(output)+ ('\n' if output else '')
