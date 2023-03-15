"""Opcode maps and other data pertaining to the MSP430 ISA"""

jumpOpcodes = {
'jne' : 0, 'jnz' : 0,
'jeq' : 1, 'jz'  : 1,
'jnc' : 2, 'jlo' : 2,
'jc'  : 3, 'jhs' : 3,
'jn'  : 4,
'jge' : 5,
'jl'  : 6,
'jmp' : 7
}

twoOpOpcodes = {
'mov'  : 4,
'add'  : 5,
'addc' : 6,
'subc' : 7,
'sub'  : 8,
'cmp'  : 9,
'dadd' : 10,
'bit'  : 11,
'bic'  : 12,
'bis'  : 13,
'xor'  : 14,
'and'  : 15
}

oneOpOpcodes = {
'rrc'  : 0,
'swpb' : 1,
'rra'  : 2,
'sxt'  : 3,
'push' : 4,
'call' : 5,
'reti' : 6
}

emulatedOpcodes = {
'ret' : 'mov @sp+, pc',
'clrc' : 'bic #1, sr',
'setc' : 'bis #1, sr',
'clrz' : 'bic #2, sr',
'setz' : 'bis #2, sr',
'clrn' : 'bic #4, sr',
'setn' : 'bis #4, sr',
'dint' : 'bic #8, sr',
'eint' : 'bis #8, sr',
'nop'  : 'mov r3, r3', #Any register would do the same
'br'   : 'mov {reg}, pc',
'pop'  : 'mov @sp+, {reg}',
'rla'  : 'add {reg}, {reg}',
'rlc'  : 'addc {reg}, {reg}',
'inv'  : 'xor #0xffff, {reg}',
'clr'  : 'mov #0, {reg}',
'tst'  : 'cmp #0, {reg}',
'dec'  : 'sub #1, {reg}',
'decd' : 'sub #2, {reg}',
'inc'  : 'add #1, {reg}',
'incd' : 'add #2, {reg}',
'adc'  : 'addc #0, {reg}',
'dadc' : 'dadd #0, {reg}',
'sbc'  : 'subc #0, {reg}',
}
