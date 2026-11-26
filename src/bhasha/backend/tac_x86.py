"""Lower the integer scalar subset of TAC directly to System V x86-64.

The source AST is checked first because printable TAC does not retain all type
information. Unsupported programs fail explicitly instead of changing meaning.
"""
import re
import subprocess
import tempfile
from dataclasses import fields, is_dataclass
from pathlib import Path

from ..ast_nodes import Function, Literal, Print, VarDecl
from .input_runtime import INPUT_RUNTIME


class TacX86Error(ValueError):
    pass


def validate(node):
    """Reject constructs for which this initial TAC backend has no lowering."""
    if isinstance(node, VarDecl) and (node.size or node.type_name in ('doshomik', 'দশমিক')):
        raise TacX86Error('TAC x86 supports integer scalars, not arrays or floats')
    if isinstance(node, Function) and (node.return_type not in ('purno', 'পূর্ণ') or any(t not in ('purno', 'পূর্ণ') for _, t in node.params)):
        raise TacX86Error('TAC x86 functions require integer parameters and return values')
    if isinstance(node, Print) and node.value.inferred_type != 'int':
        raise TacX86Error('TAC x86 prints integers only')
    if getattr(node, 'inferred_type', None) == 'float' or (isinstance(node, Literal) and isinstance(node.value, (float, str))):
        raise TacX86Error('TAC x86 does not support floats or strings')
    if is_dataclass(node):
        for field in fields(node):
            validate(getattr(node, field.name))
    elif isinstance(node, (list, tuple)):
        for item in node:
            validate(item)


class Emitter:
    def __init__(self, lines):
        self.ir = lines
        self.globals = {line[7:] for line in lines if line.startswith('global ')}
        self.global_labels = {name: f'.Lglobal{i}' for i, name in enumerate(sorted(self.globals))}
        self.function_labels = {}
        self.labels = {}
        self.out = []
        self.slots = {}
        self.params = []

    def emit(self, *lines):
        self.out.extend('  ' + line for line in lines)

    def slot(self, name):
        if name in self.global_labels:
            return f'[rip+{self.global_labels[name]}]'
        if name not in self.slots:
            self.slots[name] = 8 * (len(self.slots) + 1)
        return f'[rbp-{self.slots[name]}]'

    def atom(self, text, reg='rax'):
        if text in ('True', 'False'):
            self.emit(f'mov {reg}, {1 if text == "True" else 0}')
        elif re.fullmatch(r'-?\d+', text):
            value = int(text)
            if not -(1 << 63) <= value < (1 << 63):
                raise TacX86Error('integer literal outside signed 64-bit range')
            self.emit(f'mov {reg}, {value}')
        elif re.fullmatch(r'[^\s(),\[\]:=]+', text):
            self.emit(f'mov {reg}, QWORD PTR {self.slot(text)}')
        else:
            raise TacX86Error(f'unsupported TAC operand: {text}')

    def expr(self, text):
        parts = text.split()
        if len(parts) == 1:
            self.atom(parts[0]); return
        if len(parts) == 2 and parts[0] in ('-', 'NOT', '!'):
            self.atom(parts[1])
            if parts[0] == '-': self.emit('neg rax')
            else: self.emit('test rax, rax', 'sete al', 'movzx rax, al')
            return
        if len(parts) != 3:
            raise TacX86Error(f'unsupported TAC expression: {text}')
        left, op, right = parts
        self.atom(left, 'rax'); self.atom(right, 'rcx')
        if op in ('+', '-', '*'):
            self.emit({'+': 'add', '-': 'sub', '*': 'imul'}[op] + ' rax, rcx')
        elif op in ('/', '%'):
            self.emit('test rcx, rcx', 'jz .Ldivision_error', 'cqo', 'idiv rcx')
            if op == '%': self.emit('mov rax, rdx')
        elif op in ('==', '!=', '<', '>', '<=', '>='):
            self.emit('cmp rax, rcx', {'==':'sete','!=':'setne','<':'setl','>':'setg','<=':'setle','>=':'setge'}[op] + ' al', 'movzx rax, al')
        else:
            raise TacX86Error(f'unsupported TAC operator: {op}')

    def block(self, lines, params=(), main=False):
        self.out = []; self.slots = {}; self.params = []
        registers = ('rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9')
        for name, reg in zip(params, registers): self.emit(f'mov QWORD PTR {self.slot(name)}, {reg}')
        for index, name in enumerate(params[len(registers):]):
            self.emit(f'mov rax, QWORD PTR [rbp+{16+index*8}]', f'mov QWORD PTR {self.slot(name)}, rax')
        for line in lines:
            if line.startswith('global '): continue
            if line.endswith(':'):
                self.out.append(self.labels[line[:-1]] + ':'); continue
            if line.startswith('goto '): self.emit('jmp ' + self.labels[line[5:]]); continue
            match = re.fullmatch(r'ifFalse (.+) goto (\w+)', line)
            if match:
                self.expr(match.group(1)); self.emit('test rax, rax', 'jz ' + self.labels[match.group(2)]); continue
            if line.startswith('param '): self.params.append(line[6:]); continue
            match = re.fullmatch(r'([^\s=]+) = call ([^\s,]+), (\d+)', line)
            if match:
                dest, name, count = match.group(1), match.group(2), int(match.group(3))
                if count > len(self.params) or name not in self.function_labels: raise TacX86Error('unsupported TAC call')
                args = self.params[-count:] if count else []
                if count: del self.params[-count:]
                stack_count = max(0, count-len(registers)); padding = 8 if stack_count % 2 else 0
                if padding: self.emit('sub rsp, 8')
                for arg in reversed(args): self.atom(arg); self.emit('push rax')
                for reg in registers[:count]: self.emit('pop ' + reg)
                self.emit('call ' + self.function_labels[name])
                if stack_count or padding: self.emit(f'add rsp, {stack_count*8+padding}')
                self.emit(f'mov QWORD PTR {self.slot(dest)}, rax'); continue
            if line.startswith('print '):
                self.expr(line[6:]); self.emit('mov rsi, rax', 'lea rdi, [rip+.Lformat]', 'xor eax, eax', 'call printf'); continue
            if line.startswith('read '):
                self.emit(f'lea rdi, {self.slot(line[5:])}', 'call bh_read_int', 'cmp eax, 1', 'jne .Linput_error'); continue
            if line.startswith('return '): self.expr(line[7:]); self.emit('leave', 'ret'); continue
            match = re.fullmatch(r'decl \S+ (\S+)', line)
            if match: self.emit(f'mov QWORD PTR {self.slot(match.group(1))}, 0'); continue
            match = re.fullmatch(r'(\S+) (\+=|-=|\*=|/=|=) (.+)', line)
            if match:
                name, op, rhs = match.groups()
                self.expr(rhs if op == '=' else f'{name} {op[0]} {rhs}')
                self.emit(f'mov QWORD PTR {self.slot(name)}, rax'); continue
            raise TacX86Error(f'unsupported TAC instruction: {line}')
        if self.params: raise TacX86Error('unconsumed TAC parameters')
        if main: self.emit('xor eax, eax', 'leave', 'ret')
        else: self.emit('ud2')
        frame = (len(self.slots) * 8 + 15) // 16 * 16
        return ['  push rbp', '  mov rbp, rsp', f'  sub rsp, {frame}'] + self.out

    def generate(self):
        functions = []; main = []; active = None
        for line in self.ir:
            header = re.fullmatch(r'func ([^\s(]+)\(([^)]*)\):', line)
            if header:
                if active is not None: raise TacX86Error('nested TAC functions unsupported')
                name = header.group(1); params = [x.strip() for x in header.group(2).split(',') if x.strip()]
                self.function_labels[name] = f'.Lfunction{len(functions)}'; active = (name, params, []); functions.append(active)
            elif line == 'endfunc':
                if active is None: raise TacX86Error('unexpected endfunc')
                active = None
            else: (active[2] if active is not None else main).append(line)
        if active is not None: raise TacX86Error('missing endfunc')
        for line in self.ir:
            if re.fullmatch(r'[A-Za-z_]\w*:', line) and not line.startswith('func '):
                self.labels[line[:-1]] = f'.Lbranch{len(self.labels)}'
        result = ['.intel_syntax noprefix', '.text', '.global main', 'main:'] + self.block(main, main=True)
        for name, params, body in functions:
            result += [self.function_labels[name] + ':'] + self.block(body, params=params)
        result += ['.Ldivision_error:', '  lea rsi, [rip+.Ldivision_message]', '  mov edx, .Ldivision_end - .Ldivision_message', '  jmp .Lruntime_error', '.Linput_error:', '  lea rsi, [rip+.Linput_message]', '  mov edx, .Linput_end - .Linput_message', '.Lruntime_error:', '  mov eax, 1', '  mov edi, 2', '  syscall', '  mov edi, 2', '  call exit', '.section .rodata', '.Lformat: .string "%ld\\n"', '.Ldivision_message: .ascii "runtime error: division by zero\\n"', '.Ldivision_end:', '.Linput_message: .ascii "runtime error: invalid or missing input\\n"', '.Linput_end:', '.section .bss']
        for label in self.global_labels.values(): result += [label + ':', '  .zero 8']
        result += ['.section .note.GNU-stack,"",@progbits']
        return '\n'.join(result) + '\n'


def emit_tac_x86(tree, lines, outfile):
    validate(tree)
    assembly = Emitter(lines).generate()
    out = Path(outfile); asm = out.with_suffix('.s')
    asm.write_text(assembly, encoding='utf8')
    with tempfile.TemporaryDirectory(prefix='bhasha-tac-runtime-') as directory:
        runtime = Path(directory) / 'input.c'
        runtime.write_text(INPUT_RUNTIME, encoding='utf8')
        subprocess.run(['gcc', '-no-pie', str(asm), str(runtime), '-o', str(out)], check=True)
    return asm
