#!/usr/bin/python3
#
# Python ply study
# Python version of PPAP language processing
#
# PPAP language
#  https://github.com/yhara/ppap-lang
#
# requirements
#  ply
#

import sys

from ply import lex
from ply import yacc


keywords = (
    'I', 'Uh',
    'Replace', 'Append', 'Rip', 'Multiply', 'Chop',
    'Push', 'Pull', 'Print', 'Put', 'Pick',
    'Compare', 'Superior', 'Jump',
)

keyword_map = dict(zip(keywords, [k.upper() for k in keywords]))

tokens = tuple(keyword_map.values()) + (
    'HAVE', 'NO', 'A', 'NUMBER', 'REGISTER',
    'HYPHEN',
    'SPACE', 'NEWLINE',
    'QUESTION_MARK', 'EXCLAMATION_MARK',
)

t_HAVE = r'have'
t_NO = r'no'
t_A = r'an?'
t_HYPHEN = r'-'
t_SPACE = r'[ \t]+'
t_QUESTION_MARK = r'\?'
t_EXCLAMATION_MARK = r'!'

t_ignore_COMMENT = r'\#[^\n]*'


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_REGISTER(t):
    # r'(P|[A-OQ-Z][A-OQ-Za-oq-z0-9]*[Pp])[A-Za-z0-9]*'
    r'[A-Z][A-Za-z0-9]*'
    if t.value in keyword_map:
        t.type = keyword_map[t.value]
    return t


def t_NEWLINE(t):
    r'\r?\n'
    t.lexer.lineno += 1
    return t


def t_error(t):
    print(f"Illegal character '{t.value[0]}'", file=sys.stderr)
    t.lexer.skip(1)


lexobj = lex.lex(debug=0)

register_names = []
label_names = []


def add_program(p, program):
    p[0].append(program)
    if program[0] == 'REGISTER':
        if program[1] not in register_names:
            register_names.append(program[1])
    elif program[0] == 'LABEL':
        if program[1] not in register_names:
            label_names.append(program[1])
        else:
            print(f"'{program[1]}' label already exists", file=sys.stderr)


def p_program(p):
    '''program : program line
               | line'''
    if len(p) == 3:
        p[0] = p[1]
        if p[0] is not None and p[2]:
            add_program(p, p[2])
    else:
        p[0] = []
        if p[1]:
            add_program(p, p[1])


def p_program_error(p):
    '''program : error'''
    value = p[1].value
    if p[1].type == 'NEWLINE':
        value = '\\n'
    print(f"line {p[1].lineno}: '{value}' syntax error", file=sys.stderr)
    p[0] = None
    p.parser.error = 1


def p_line(p):
    '''line : empty_or_space register_declaration empty_or_space NEWLINE
            | empty_or_space label empty_or_space NEWLINE
            | empty_or_space uh SPACE label empty_or_space NEWLINE
            | empty_or_space uh SPACE command empty_or_space NEWLINE
            | empty_or_space NEWLINE'''
    if len(p) == 5:
        p[0] = p[2]
    elif len(p) == 7:  # Uh! label
        p[0] = p[4]
    else:
        p[0] = None


def p_uh(p):
    '''uh : UH EXCLAMATION_MARK'''
    pass


def p_empty_or_space(p):
    '''empty_or_space :
                      | SPACE'''
    pass


def p_register_declaration(p):
    '''register_declaration : I SPACE HAVE SPACE number SPACE REGISTER
                            | I SPACE HAVE SPACE REGISTER'''
    if len(p) == 8:
        name = p[7]
        value = p[5]
        lineno = p.lineno(7)
    else:
        name = p[5]
        value = 0
        lineno = p.lineno(5)
    if 'p' not in name.lower():
        print(f"line {lineno}: '{name}' does not include 'p' or 'P'", file=sys.stderr)
    p[0] = ('REGISTER', name, value)


def p_number(p):
    '''number : NO
              | A
              | NUMBER'''
    if isinstance(p[1], int):
        p[0] = p[1]
    elif p[1][0] == 'a':
        p[0] = 1
    else:  # no
        p[0] = 0


def p_label(p):
    '''label : label HYPHEN register
             | register HYPHEN register'''
    if p[1] and p[3]:
        if isinstance(p[1], tuple):
            label = p[1][1]
        else:
            label = p[1]
        p[0] = ('LABEL', label + '-' + p[3])
    else:
        p[0] = None


def p_register(p):
    '''register : REGISTER'''
    if p[1] not in register_names:  # confirmation of register-name
        print(f"line {p.lineno(1)}: '{p[1]}' is an undeclared register", file=sys.stderr)
    p[0] = p[1]


def p_command(p):
    '''command : replace
               | append
               | rip
               | multiply
               | chop
               | push
               | pull
               | print
               | put
               | pick
               | compare
               | superior
               | jump'''
    p[0] = p[1]


def p_replace(p):
    '''replace : REPLACE HYPHEN register HYPHEN register'''
    if p[3] and p[5]:
        p[0] = ('MOV', p[3], p[5])
    else:
        p[0] = None


def p_append(p):
    '''append : APPEND HYPHEN register HYPHEN register'''
    if p[3] and p[5]:
        p[0] = ('ADD', p[3], p[5])
    else:
        p[0] = None


def p_rip(p):
    '''rip : RIP HYPHEN register HYPHEN register'''
    if p[3] and p[5]:
        p[0] = ('SUB', p[3], p[5])
    else:
        p[0] = None


def p_multiply(p):
    '''multiply : MULTIPLY HYPHEN register HYPHEN register'''
    if p[3] and p[5]:
        p[0] = ('MUL', p[3], p[5])
    else:
        p[0] = None


def p_chop(p):
    '''chop : CHOP HYPHEN register HYPHEN register'''
    if p[3] and p[5]:
        p[0] = ('DIV', p[3], p[5])
    else:
        p[0] = None


def p_push(p):
    '''push : PUSH HYPHEN register HYPHEN register'''
    if p[3] and p[5]:
        p[0] = ('STORE', p[3], p[5])
    else:
        p[0] = None


def p_pull(p):
    '''pull : PULL HYPHEN register HYPHEN register'''
    if p[3] and p[5]:
        p[0] = ('LOAD', p[3], p[5])
    else:
        p[0] = None


def p_print(p):
    '''print : PRINT HYPHEN register'''
    if p[3]:
        p[0] = ('PRINT', p[3])
    else:
        p[0] = None


def p_put(p):
    '''put : PUT HYPHEN registers'''
    if p[3]:
        p[0] = ('PUTC',) + p[3]
    else:
        p[0] = None


def p_registers(p):
    '''registers : registers HYPHEN register
                 | register'''
    if len(p) == 4:
        if p[1] and p[3]:
            p[0] = p[1] + (p[3],)
        else:
            p[0] = None
    else:
        if p[1]:
            p[0] = (p[1],)
        else:
            p[0] = None


def p_pick(p):
    '''pick : PICK HYPHEN register'''
    if p[3]:
        p[0] = ('GETC', p[3])
    else:
        p[0] = None


def p_compare(p):
    '''compare : COMPARE HYPHEN register HYPHEN register
               | COMPARE HYPHEN register HYPHEN register QUESTION_MARK
               | COMPARE HYPHEN register HYPHEN register HYPHEN label EXCLAMATION_MARK
               | COMPARE HYPHEN register HYPHEN register HYPHEN label EXCLAMATION_MARK QUESTION_MARK'''
    if len(p) == 6:
        if p[3] and p[5]:
            p[0] = ('EQ', p[3], p[5])
        else:
            p[0] = None
    elif len(p) == 7:
        if p[3] and p[5]:
            p[0] = ('NE', p[3], p[5])
        else:
            p[0] = None
    elif len(p) == 9:
        if p[3] and p[5] and p[7]:
            p[0] = ('JEQ', p[3], p[5], p[7][1])
        else:
            p[0] = None
    else:  # len(p) == 10:
        if p[3] and p[5] and p[7]:
            p[0] = ('JNE', p[3], p[5], p[7][1])
        else:
            p[0] = None


def p_superior(p):
    '''superior : SUPERIOR HYPHEN register HYPHEN register
                | SUPERIOR HYPHEN register HYPHEN register QUESTION_MARK
                | SUPERIOR HYPHEN register HYPHEN register HYPHEN label EXCLAMATION_MARK
                | SUPERIOR HYPHEN register HYPHEN register HYPHEN label EXCLAMATION_MARK QUESTION_MARK'''
    if len(p) == 6:
        if p[3] and p[5]:
            p[0] = ('GT', p[3], p[5])
        else:
            p[0] = None
    elif len(p) == 7:
        if p[3] and p[5]:
            p[0] = ('GE', p[3], p[5])
        else:
            p[0] = None
    elif len(p) == 9:
        if p[3] and p[5] and p[7]:
            p[0] = ('JGT', p[3], p[5], p[7][1])
        else:
            p[0] = None
    else:  # len(p) == 10:
        if p[3] and p[5] and p[7]:
            p[0] = ('JGE', p[3], p[5], p[7][1])
        else:
            p[0] = None


def p_jump(p):
    '''jump : JUMP HYPHEN label'''
    if p[3]:
        p[0] = ('JMP', p[3][1])
    else:
        p[0] = None


def p_error(p):
    if not p:
        print("syntax error at eof", file=sys.stderr)


parser = yacc.yacc(debug=False)


def parse(data, debug=False):
    global register_names
    global label_names
    register_names = []
    label_names = []
    lexobj.lineno = 1
    parser.error = 0
    p = parser.parse(data, debug=debug)
    if parser.error:
        return None
    return p


def run(data, debug=False):
    label_map = {}
    pc = 0
    for i, op in enumerate(data):
        if op[0] == 'LABEL':
            label_map[op[1]] = i
    pc = 0
    registers = {}
    memory = {}
    memory_size = 1 << 24
    while pc < len(data):
        op = data[pc]
        pc += 1
        if op[0] == 'REGISTER':
            registers[op[1]] = op[2]
            continue
        if op[0] == 'LABEL':
            continue
        if op[0] == 'MOV':
            registers[op[1]] = registers[op[2]]
            continue
        if op[0] == 'ADD':
            registers[op[1]] += registers[op[2]]
            continue
        if op[0] == 'SUB':
            registers[op[1]] -= registers[op[2]]
            continue
        if op[0] == 'MUL':
            registers[op[1]] *= registers[op[2]]
            continue
        if op[0] == 'DIV':
            registers[op[1]] = int(registers[op[1]] / registers[op[2]])
            continue
        if op[0] == 'STORE':
            addr = registers[op[2]]
            if addr >= memory_size or addr < 0:
                raise ValueError('memory address to store is out of range')
            memory[addr] = registers[op[1]]
            continue
        if op[0] == 'LOAD':
            addr = registers[op[2]]
            if addr >= memory_size or addr < 0:
                raise ValueError('memory address to load is out of range')
            registers[op[1]] = memory.get(addr, 0)
            continue
        if op[0] == 'PRINT':
            print(f'{registers[op[1]]}', end='', flush=True)
            continue
        if op[0] == 'PUTC':
            for i in range(1, len(op)):
                c = registers[op[i]]
                print(chr(c), end='', flush=True)
            continue
        if op[0] == 'GETC':
            c = sys.stdin.read(1)
            registers[op[1]] = ord(c)
            continue
        if op[0] == 'EQ':
            registers[op[1]] = 1 if registers[op[1]] == registers[op[2]] else 0
            continue
        if op[0] == 'JEQ':
            if registers[op[1]] == registers[op[2]]:
                pc = label_map[op[3]]
            continue
        if op[0] == 'NE':
            registers[op[1]] = 1 if registers[op[1]] != registers[op[2]] else 0
            continue
        if op[0] == 'JNE':
            if registers[op[1]] != registers[op[2]]:
                pc = label_map[op[3]]
            continue
        if op[0] == 'GT':
            registers[op[1]] = 1 if registers[op[1]] > registers[op[2]] else 0
            continue
        if op[0] == 'JGT':
            if registers[op[1]] > registers[op[2]]:
                pc = label_map[op[3]]
            continue
        if op[0] == 'GE':
            registers[op[1]] = 1 if registers[op[1]] >= registers[op[2]] else 0
            continue
        if op[0] == 'JGE':
            if registers[op[1]] >= registers[op[2]]:
                pc = label_map[op[3]]
            continue
        if op[0] == 'JMP':
            pc = label_map[op[1]]
            continue


def to_c(data, debug=False):
    register_names = []
    need_memory = False
    print('#include <stdio.h>\n#include <stdlib.h>\n\nint main(void) {')
    for op in data:
        if op[0] == 'REGISTER':
            if op[1] not in register_names:
                register_names.append(op[1])
                print(f'    int {op[1]};')
        if op[0] == 'STORE' or op[0] == 'LOAD':
            need_memory = True
    print('')
    if need_memory:
        print('#define MEMORY_SIZE (1 << 24)')
        print('    int *memory = calloc(MEMORY_SIZE, sizeof(int));\n')

    def c_label(label):
        return '_'.join(label.split('-'))

    def ternary_operator(op, cond):
        print(f'    {op[1]} = ({op[1]} {cond} {op[2]} ? 1 : 0)')

    def conditional_jump(op, cond):
        print(f'    if ({op[1]} {cond} {op[2]}) {{\n        goto {c_label(op[3])};\n    }}')

    for op in data:
        if op[0] == 'REGISTER':
            print(f'    {op[1]} = {op[2]};')
            continue
        if op[0] == 'LABEL':
            print(f'\n{c_label(op[1])}:')
            continue
        if op[0] == 'MOV':
            print(f'    {op[1]} = {op[2]};')
            continue
        if op[0] == 'ADD':
            print(f'    {op[1]} += {op[2]};')
            continue
        if op[0] == 'SUB':
            print(f'    {op[1]} -= {op[2]};')
            continue
        if op[0] == 'MUL':
            print(f'    {op[1]} *= {op[2]};')
            continue
        if op[0] == 'DIV':
            print(f'    {op[1]} /= {op[2]};')
            continue
        if op[0] == 'STORE':
            print(f'    memory[{op[2]}] = {op[1]};')
            continue
        if op[0] == 'LOAD':
            print(f'    {op[1]} = memory[{op[2]}];')
            continue
        if op[0] == 'PRINT':
            print(f'    printf("%d", {op[1]});')
            continue
        if op[0] == 'PUTC':
            for i in range(1, len(op)):
                print(f'    putchar({op[i]});')
            continue
        if op[0] == 'GETC':
            print(f'    {op[1]} = getchar();')
            continue
        if op[0] == 'EQ':
            ternary_operator(op, '==')
            continue
        if op[0] == 'JEQ':
            conditional_jump(op, '==')
            continue
        if op[0] == 'NE':
            ternary_operator(op, '!=')
            continue
        if op[0] == 'JNE':
            conditional_jump(op, '!=')
            continue
        if op[0] == 'GT':
            ternary_operator(op, '>')
            continue
        if op[0] == 'JGT':
            conditional_jump(op, '>')
            continue
        if op[0] == 'GE':
            ternary_operator(op, '>=')
            continue
        if op[0] == 'JGE':
            conditional_jump(op, '>=')
            continue
        if op[0] == 'JMP':
            print(f'    goto {c_label(op[1])};')
            continue
    print('    return 0;\n}')


if __name__ == '__main__':
    import argparse

    argpparser = argparse.ArgumentParser()
    argpparser.add_argument('-d', '--debug', action='store_true')
    argpparser.add_argument('--to-c', '--to_c', action='store_true')
    argpparser.add_argument('file', type=argparse.FileType('r'), default=sys.stdin)
    args = argpparser.parse_args()
    data = args.file.read()
    res = parse(data, debug=args.debug)
    if res:
        if args.to_c:
            to_c(res, debug=args.debug)
        elif res:
            run(res, debug=args.debug)
