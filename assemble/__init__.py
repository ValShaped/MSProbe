from assemble.rule_processor import preprocessor, postprocessor
from common import *
from common.isa_data import *
from .errors import *

import sys
import pdb
import re

PC = 0  #Incremented by each instruction, incremented in words NOT bytes
labels = {} #Label name and its PC location
"""
`labels` are a label name, followed by a the address of the label relative to the loadaddr
"""
jumps = {} #PC location of jump and its corresponding label
"""
`jumps` are the address of a jump instruction and its corresponding label
During jump resolution, each jump in jumps is modified with a relative offset
Example jump:
{0: 'loop'}
"""
output = [] #Output hex

def asmMain(assembly, outfile=None, silent=False, allowFail=True):
	global PC #Get PC

	outFP = open(outfile, 'w') if outfile else None

	if not assembly:
		#Provide a prompt for entry
		instructions = ''
		ins = ''
		print('Input assembly. Terminate input with the ".end" directive, or Ctrl+D (EOF).')
		while True:
			ins = sys.stdin.readline()
			if ins == '.end\n' or ins == '':
				break
			instructions = instructions + ins
	else:
		with open(assembly) as fp:
			instructions = fp.read()

	def labelRegisterRule(ins: str) -> str:
		if ':' in ins:
			try:
				registerLabel(ins)
			except RedefinedLabelError as exp:
				print('Label "' + exp.name + '" at line number ' + str(lineNumber + 1) + ' already defined',
					file=sys.stderr)
				if not allowFail: sys.exit(-1)
			return ""
		return ins

	#Register the default preprocessor rules
	for rule in [(lambda ins: re.split(r'\s*(//|;)', ins)[0]), registerLabel]:
		preprocessor.register(rule)

	#Register the default postprocessor rules
	for rule in {}:
		postprocessor.register(rule)

	for lineNumber, ins in enumerate(instructions.splitlines()):
		#Strip leading and trailing whitespace
		ins = ins.strip()

		#Handle preprocessor substitution rules
		#Skip empty lines or lines beginning with a comment

		try:
			#Handle preprocessor rules (.directives, comment removal, 'label:' definition)
			ins = preprocessor(ins) #raises RedefinedLabelError if label redefined
			if ins is None:
				break
			if len(ins) == 0 or ins.startswith((';', '//')):
				continue
			if not silent: print(f"{lineNumber + 1:>4}| {ins}")
			assemble(ins)
		except AssemblyError as exp:
			ins = highlight(ins, exp.name)
			print(exp.pretty_print(lineNumber, ins), file=sys.stderr)
			if not allowFail: sys.exit(-1)

	#Handle postprocessor hooks.
	#These functions manipulate the raw output data, and perform tasks such as link resolution
	postprocessor(output)

	#Output the object as hex
	for i in output:
		if not silent:
			print(hexrep(i), end='', file=sys.stdout)# + ' (' + bitrep(i, 16) + ')')
		if outFP:
			print(hexrep(i), end='', file=outFP)
	if not silent: print('', file=sys.stdout) #End hex representation with a newline
	if outFP:
		outFP.close()

def resolveJumps(_):
	"""Resolve pending jumps in the jumps list"""
	global labels, jumps, output
	#Resolve jump labels
	for pc, label in jumps.items():
		try:
			labelpos = labels[label]
		except KeyError:
			print(f'Label "{label}" does not exist, but a jump instruction attempts to jump to it',
				file=sys.stderr)
			sys.exit(-1)
		#Modify the jump instruction
		#Get in little-endian format
		ins = hexrep(output[pc])
		ins = int(ins[2:4] + ins[0:2], 16)
		ins = [bit for bit in bitrep(ins, 16)]
		offset = (labelpos - pc) * 2 #Words versus bytes
		#Jump offsets are multiplied by two, added by two (PC increment), and sign extendedB
		ins[6:] = bitrep((offset - 2) // 2, 10)
		#Output again in little endian
		strword = hexrep(int(''.join(str(e) for e in ins), 2), 4)
		output[pc] = int(strword[2:] + strword[0:2], 16)

#TODO: Resolve labels in calls

def registerLabel(ins: str):
	"""Registers a label for later replacement"""
	global labels #Get labels
	global PC #Get PC
	if ':' in ins:
		label, addr = ins.split(sep=':')
		if label in labels:
			raise RedefinedLabelError(label)
		labels[label] = int(addr) if addr != '' else PC
		return ""
	return ins

def registerJumpInstruction(PC, label):
	"""Defer jump offset calculation until labels are defined"""
	global jumps #Get jump instructions
	jumps[PC] = label
	postprocessor.register(resolveJumps)

def assemble(ins):
	"""Assemble a single instruction, and append results to the output stream."""
	opcode, _ = getOpcode(ins)
	if opcode in jumpOpcodes:
		return assembleJumpInstruction(ins)
	elif opcode in oneOpOpcodes:
		return assembleOneOpInstruction(ins)
	elif opcode in twoOpOpcodes:
		return assembleTwoOpInstruction(ins)
	elif opcode in emulatedOpcodes:
		return assembleEmulatedInstruction(ins)
	else:
		raise OpcodeError(opcode)

def assembleEmulatedInstruction(ins):
	"""Assembles a zero- or one-operand 'emulated' instruction."""
	#Emulated instructions are either zero or one operand instructions.
	opcode, _ = getOpcode(ins)
	if '{reg}' in emulatedOpcodes[opcode]:
		register = ins[ins.find(' ') + 1 : ]
		ins = emulatedOpcodes[opcode].format(reg=register)
	else:
		ins = emulatedOpcodes[opcode]
	return assemble(ins)

def assembleOneOpInstruction(ins):
	"""Assembles a one-operand (format I) instruction."""
	#     [one op identifier|opcode |wB |Ad   |dest      ]
	out = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	out[0:6] = '000100' #One op identifier

	opcode, byteMode = getOpcode(ins)
	out[6:9] = bitrep(oneOpOpcodes[opcode], 3)
	out[9] = bitrep(byteMode, 1)

	#Figure out where the operand is
	start = ins.find(' ') + 1
	reg = ins[start :]

	#We need to provide the opcode here to detect the push bug; see the function itself
	extensionWord, adrmode, regID = assembleRegister(reg, opcode=opcode)

	out[10:12] = bitrep(adrmode, 2)
	out[12:] = bitrep(regID, 4)
	appendWord(int(''.join(str(e) for e in out), 2))
	if extensionWord:
		appendWord(int(extensionWord, 16))

def sample_getOpcode(ins: str):
	op = re.findall(r'([&#@(\w.)+]+)', ins)
	#TODO: verbosity?
	print (f'\n{op}', file=sys.stderr)


def assembleTwoOpInstruction(ins):
	"""Assembles a two-operand (format III) instruction."""
	"""[0:opcode(4):3, 4:src(4):7, 8:destmode(1):8 , 9:bytemode(1):9, 10:srcmode(2):11, 12:dest(4):15]"""
	#     [opcode,  src,     Ad,bW,As,  dest   ]
	out = [0,0,0,0, 0,0,0,0, 0, 0, 0,0, 0,0,0,0]

	opcode, byteMode = getOpcode(ins)
	out[0:4] = bitrep(twoOpOpcodes[opcode], 4)
	out[9] = bitrep(byteMode, 1)

	#Find the location of the first operand
	start = ins.find(' ') + 1
	end = ins.find(',')
	regSrc = ins[start : end]

	extensionWordSrc, adrmodeSrc, regIDSrc = assembleRegister(regSrc)

	out[10:12] = bitrep(adrmodeSrc, 2)
	out[4:8] = bitrep(regIDSrc, 4)

	#Figure out where the comment is
	start = end + 2 #Right after the comma, and the space after the comma
	regDest = ins[start :]

	extensionWordDest, adrmodeDest, regIDDest = assembleRegister(regDest, isDestReg = True)

	out[8] = bitrep(adrmodeDest, 1)
	out[12:] = bitrep(regIDDest, 4)

	appendWord(int(''.join(str(e) for e in out), 2))
	if extensionWordSrc:
		appendWord(int(extensionWordSrc, 16))
	if extensionWordDest:
		appendWord(int(extensionWordDest, 16))

def assembleJumpInstruction(ins):
	"""Assembles a jump instruction. If the offset is supplied, it is assembled
	immediately. Otherwise, if a label is provided, resolution of the offset is delayed
	so that all labels can be read (including those further ahead in the instruction stream)."""
	out = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	out[0:3] = '001' #Jump identifier
	opcode, byteMode = getOpcode(ins)

	if byteMode: #Cannot have "jmp.b", how does that even make sense
		raise OpcodeError(opcode + '.b')

	out[3:6] = bitrep(jumpOpcodes[opcode], 3)

	#Figure out where the operand is
	start = ins.find(' ') + 1
	dest = ''.join(ins[start :].split()) #Remove whitespace

	#Is this a number?
	if isHexadecimal(dest):
		offset = int(dest, 16)
		if offset % 2 != 0:
			raise JumpOffsetError(dest, 'Jump offset cannot be odd.')
		if offset <= -0x3fe or offset >= 0x400:
			raise JumpOffsetError(dest, 'Jump offset out of range. Range is -3fe bytes through +400 bytes.')
		#Jump offsets are multiplied by two, added by two (PC increment), and sign extended
		out[6:] = bitrep((offset - 2) // 2, 10)
	else:
		registerJumpInstruction(PC, dest)

	appendWord(int(''.join(str(e) for e in out), 2))

def getRegister (registerName: str) -> int:
	"""Decodes register names. Returns the register index if registerName is valid, or raises RegisterError"""
	registers = {
		'pc':  0,  'sp':  1,  'sr':  2,  'cg':  3,
		'r0':  0,  'r1':  1,  'r2':  2,  'r3':  3,
		'r4':  4,  'r5':  5,  'r6':  6,  'r7':  7,
		'r8':  8,  'r9':  9,  'r10': 10, 'r11': 11,
		'r12': 12, 'r13': 13, 'r14': 14, 'r15': 15,
	}
	if registerName in registers:
		return registers[registerName]
	elif re.match(r'r[\d]+', registerName):
		raise RegisterError(registerName, 'Registers span from r0 to r15 inclusive.')
	else:
		raise RegisterError(registerName)

def getOpcode(ins: str):
	"""Returns the opcode and whether byte mode is being used."""
	#Split the opcode on characters that can't be used in an identifier
	#Example: [mov].b r15, r15
	opcode = re.split(r'[\.\W]', ins)[0]
	byteMode = False
	if '.b' in ins:
		byteMode = True
	return opcode, byteMode

def appendWord(word: int):
	"""Add a word to the output instruction stream, handling little endian format."""
	global PC #Get PC
	global output #Get output
	#Append in little-endian format
	strword = hexrep(word, 4)
	output.append(int(strword[2:] + strword[0:2], 16))
	PC += 1

def assembleRegister(reg: str, opcode=None, isDestReg = False):
	"""Assembles an operand, returning the extension word used (if applicable),
	the addressing mode, and the register ID."""
	extensionWord = None
	adrmode = 0
	regID = 0
	# Split into tokens:  (adrmodes |     registers     |     numbers)
	tokens = re.findall(r'([&#@()+]+|r[0-9]+|pc|sp|sr|cg|[x\dA-Fa-f]+)', reg)
	tokenBefore = lambda token: tokens[tokens.index(token) - 1]
	tokenAfter  = lambda token: tokens[tokens.index(token) + 1]

	#TODO Verbosity?
	# print(f'{reg:>10}: {tokens}', file=sys.stderr)

	if '(' in tokens: #Indexed mode (mode 1)
		if ')' not in tokens:
			raise AddressingModeError(reg, 'Unmatched parentheses.')
		extensionWord: str = tokenBefore('(')
		if not isHexadecimal(extensionWord):
			raise AddressingModeError(reg, 'Index is required in indexed mode.')
		if tokenAfter('(') != tokenBefore(')'):
			raise AddressingModeError(reg, 'Exactly one register is required in indexed mode.')
		adrmode = 1
		regID = getRegister(tokenAfter('('))
	elif ')' in tokens:
		raise AddressingModeError(reg, 'Unmatched parentheses.')
	elif '@' in tokens and '+' in tokens: #Indirect with post-increment mode (mode 3)
		#Destinations don't support indirect or indirect + post-increment.
		if isDestReg:
			raise AddressingModeError(reg,
				'Cannot use indirect with post-increment form for destination register.')
		regID, adrmode = getRegister(tokenAfter('@')), 3
	elif '@' in reg: #Indirect mode (mode 2)
		#Destinations don't support indirect or indirect + post-increment.
		#Indirect can be faked with an index of 0. What a waste.
		if isDestReg:
			adrmode, extensionWord = 1, 0
		else:
			adrmode = 2
		regID = getRegister(tokenAfter('@'))
	elif '#' in tokens: #Use PC to specify an immediate constant
		if isDestReg:
			raise AddressingModeError(reg,
				'Because immediates are encoded as @pc+, immediates cannot be used for ' +
				'destinations.\nConsider using &dest absolute addressing form instead.')
		regID, adrmode = 0, 3
		constant = tokenAfter('#').casefold()

		#This might be an immediate constant supported by the hardware

		#A CPU bug prevents push #4 and push #8 with r2/SR encoding from working,
		#so one must simply use a 16-bit immediate there (what a waste, again)

		if constant == '-1' or 'ffff' in constant:
			regID, adrmode = 3, 3
		elif constant == '0':
			regID, adrmode = 3, 0
		elif constant == '1':
			regID, adrmode = 3, 1
		elif constant == '2':
			regID, adrmode = 3, 2
		elif constant == '4' and opcode != 'push':
			regID, adrmode = 2, 2
		elif constant == '8' and opcode != 'push':
			regID, adrmode = 2, 3
		else:
			extensionWord = constant
	elif '&' in tokens: #Direct addressing. An extension word is fetched and used as the raw address.
		if tokens.count == tokens.index('&'):
			raise AddressingModeError(reg, 'Direct addressing mode requires an address.')
		extensionWord = tokenAfter('&') # tokens[tokens.index('&') + 1]
		regID = 2
		adrmode = 1
		#extensionWord = reg[reg.find('&') + 1 : ]
		if not isHexadecimal(extensionWord):
			raise AddressingModeError(reg, 'Invalid absolute address. Format is &addr where addr is hexadecimal.')
	else: #Regular register access (mode 0)
		adrmode = 0
		regID = getRegister(tokens[0])

	#print(f'{extensionWord=}, {adrmode=}, {regID=}', file=sys.stderr)
	return extensionWord, adrmode, regID
